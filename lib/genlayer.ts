import { createAccount, createClient } from "genlayer-js";
import { studionet, testnetAsimov, testnetBradbury, localnet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

type ChainName = "studionet" | "testnetAsimov" | "testnetBradbury" | "localnet";

const chains = {
  studionet,
  testnetAsimov,
  testnetBradbury,
  localnet
};

export const CONTRACT_ADDRESS =
  process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ||
  "0xB29bfB945A8B32e00fC4125DB7AF78e2c1385A3C";

export const CHAIN_NAME = (process.env.NEXT_PUBLIC_GENLAYER_CHAIN || "studionet") as ChainName;

function getChain() {
  return chains[CHAIN_NAME] || studionet;
}

export function createReadClient() {
  return createClient({
    chain: getChain(),
    account: createAccount()
  });
}

export async function createWalletClient() {
  if (typeof window === "undefined") {
    throw new Error("Wallet access is only available in the browser.");
  }

  const ethereum = window.ethereum;
  if (!ethereum) {
    throw new Error("No browser wallet found. Install MetaMask or another EIP-1193 wallet.");
  }

  const accounts = (await ethereum.request({
    method: "eth_requestAccounts"
  })) as string[];

  const account = accounts[0];
  if (!account) {
    throw new Error("Wallet did not return an account.");
  }

  const client = createClient({
    chain: getChain(),
    account: account as `0x${string}`,
    provider: ethereum
  }) as any;

  if (typeof client.connect === "function") {
    await client.connect(CHAIN_NAME);
  }

  return { client, account };
}

export async function readContract(functionName: string, args: unknown[] = []) {
  const client = createReadClient();
  return client.readContract({
    address: CONTRACT_ADDRESS as `0x${string}`,
    functionName,
    args: args as any[]
  });
}

export async function writeContract(functionName: string, args: unknown[] = []) {
  const { client, account } = await createWalletClient();
  const hash = await client.writeContract({
    address: CONTRACT_ADDRESS as `0x${string}`,
    functionName,
    args: args as any[],
    value: BigInt(0)
  });

  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    interval: 5_000,
    retries: 24
  });

  return {
    account,
    hash,
    receipt
  };
}

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: unknown[] | Record<string, unknown> }) => Promise<unknown>;
    };
  }
}
