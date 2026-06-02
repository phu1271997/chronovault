"use client";

import {
  BadgeCheck,
  FileSearch,
  Gavel,
  History,
  Landmark,
  Loader2,
  Scale,
  ShieldAlert,
  Sparkles,
  Wallet
} from "lucide-react";
import { FormEvent, ReactNode, useMemo, useState } from "react";
import { CHAIN_NAME, CONTRACT_ADDRESS, readContract, writeContract } from "@/lib/genlayer";

type TabKey = "lookup" | "sanction" | "petition" | "appeal";

type ResultState = {
  title: string;
  value: unknown;
  tone?: "good" | "warn" | "bad";
};

const nowSeconds = () => Math.floor(Date.now() / 1000).toString();

function pretty(value: unknown) {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(
    value,
    (_key, item) => (typeof item === "bigint" ? item.toString() : item),
    2
  );
}

function linesToArray(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function ResultPanel({ result }: { result: ResultState | null }) {
  if (!result) return null;

  return (
    <div className="result">
      <div className="result-header">
        <span>{result.title}</span>
        <span className={`status ${result.tone || "good"}`}>
          <BadgeCheck size={16} />
          Live response
        </span>
      </div>
      <pre>{pretty(result.value)}</pre>
    </div>
  );
}

function Field({
  label,
  children,
  full = false
}: {
  label: string;
  children: ReactNode;
  full?: boolean;
}) {
  return (
    <div className={`field ${full ? "full" : ""}`}>
      <label>{label}</label>
      {children}
    </div>
  );
}

export default function Home() {
  const [tab, setTab] = useState<TabKey>("lookup");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ResultState | null>(null);
  const [wallet, setWallet] = useState("");

  const [lookupAddress, setLookupAddress] = useState("");
  const [sanctionId, setSanctionId] = useState("1");

  const [offender, setOffender] = useState("");
  const [reason, setReason] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [severity, setSeverity] = useState("3");
  const [sanctionTimestamp, setSanctionTimestamp] = useState(nowSeconds());

  const [petitionId, setPetitionId] = useState("1");
  const [supportingUrls, setSupportingUrls] = useState("");
  const [chainHistoryUrl, setChainHistoryUrl] = useState("");
  const [petitionTimestamp, setPetitionTimestamp] = useState(nowSeconds());

  const [appealSanctionId, setAppealSanctionId] = useState("1");
  const [appealReason, setAppealReason] = useState("");
  const [appealTimestamp, setAppealTimestamp] = useState(nowSeconds());

  const shortAddress = useMemo(() => {
    if (!CONTRACT_ADDRESS) return "Missing contract address";
    return `${CONTRACT_ADDRESS.slice(0, 10)}...${CONTRACT_ADDRESS.slice(-8)}`;
  }, []);

  async function run(title: string, fn: () => Promise<unknown>, tone: ResultState["tone"] = "good") {
    setBusy(true);
    setResult(null);
    try {
      const value = await fn();
      if (
        value &&
        typeof value === "object" &&
        "account" in value &&
        typeof (value as { account?: unknown }).account === "string"
      ) {
        setWallet((value as { account: string }).account);
      }
      setResult({ title, value, tone });
    } catch (error) {
      setResult({
        title: "Request failed",
        value: error instanceof Error ? error.message : String(error),
        tone: "bad"
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleLookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("Address status", () => readContract("check_address_status", [lookupAddress]));
  }

  async function handleHistory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("Sanction history", () => readContract("get_sanction_history", [lookupAddress]));
  }

  async function handleVerdict(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("Latest verdict", () =>
      readContract("get_redemption_verdict", [BigInt(sanctionId)])
    );
  }

  async function handleRecordSanction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("Sanction transaction accepted", () =>
      writeContract("record_sanction", [
        offender,
        reason,
        evidenceUrl,
        Number(severity),
        BigInt(sanctionTimestamp)
      ])
    );
  }

  async function handlePetition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run(
      "Redemption petition transaction accepted",
      () =>
        writeContract("petition_for_redemption", [
          BigInt(petitionId),
          linesToArray(supportingUrls),
          chainHistoryUrl,
          BigInt(petitionTimestamp)
        ]),
      "warn"
    );
  }

  async function handleAppeal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run(
      "Appeal transaction accepted",
      () =>
        writeContract("appeal_verdict", [
          BigInt(appealSanctionId),
          appealReason,
          BigInt(appealTimestamp)
        ]),
      "warn"
    );
  }

  const tabs = [
    { key: "lookup" as const, label: "Public lookup", icon: FileSearch },
    { key: "sanction" as const, label: "Record sanction", icon: ShieldAlert },
    { key: "petition" as const, label: "Petition redemption", icon: Scale },
    { key: "appeal" as const, label: "Appeal verdict", icon: Gavel }
  ];

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Landmark size={22} />
          </div>
          <div>
            <h1>ChronoVault</h1>
            <p>Evidence-based redemption for Web3 reputation systems</p>
          </div>
        </div>
        <div className="contract-pill" title={CONTRACT_ADDRESS}>
          <span className="dot" />
          {CHAIN_NAME} contract: {shortAddress}
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <div className="brief">
            <h2>The right to be remembered fairly.</h2>
            <p>
              ChronoVault connects to a live GenLayer Intelligent Contract that records
              sanctions, evaluates redemption petitions with public evidence, and preserves
              every verdict as transparent on-chain history.
            </p>
          </div>
          <div className="verdict-band">
            <div>
              <span>AI Parole Officer</span>
              <strong>Redeem without erasing history.</strong>
            </div>
            <div>
              <span>Live contract</span>
              <strong>{shortAddress}</strong>
            </div>
          </div>
        </section>

        <section className="metrics">
          <div className="metric">
            <span>Network</span>
            <strong>{CHAIN_NAME}</strong>
          </div>
          <div className="metric">
            <span>Cooldown</span>
            <strong>180 days</strong>
          </div>
          <div className="metric">
            <span>Redemption</span>
            <strong>80+</strong>
          </div>
          <div className="metric">
            <span>Wallet</span>
            <strong>{wallet ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}` : "Not connected"}</strong>
          </div>
        </section>

        <section className="workspace">
          <nav className="side" aria-label="ChronoVault actions">
            {tabs.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  className={`tab ${tab === item.key ? "active" : ""}`}
                  key={item.key}
                  onClick={() => {
                    setTab(item.key);
                    setResult(null);
                  }}
                  type="button"
                >
                  <Icon size={18} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="panel">
            {tab === "lookup" && (
              <>
                <div className="panel-header">
                  <div>
                    <h3>Public lookup</h3>
                    <p>Read live address status, full sanction history, or the latest AI verdict.</p>
                  </div>
                </div>
                <form className="grid" onSubmit={handleLookup}>
                  <Field label="Address" full>
                    <input
                      placeholder="0x..."
                      value={lookupAddress}
                      onChange={(event) => setLookupAddress(event.target.value)}
                      required
                    />
                  </Field>
                  <div className="actions">
                    <button className="button" disabled={busy} type="submit">
                      {busy ? <Loader2 size={17} className="spin" /> : <FileSearch size={17} />}
                      Check status
                    </button>
                    <button
                      className="button ghost"
                      disabled={busy}
                      onClick={(event) => handleHistory(event as unknown as FormEvent<HTMLFormElement>)}
                      type="button"
                    >
                      <History size={17} />
                      Load history
                    </button>
                  </div>
                </form>
                <form className="grid" onSubmit={handleVerdict}>
                  <Field label="Sanction ID" full>
                    <input
                      min="1"
                      type="number"
                      value={sanctionId}
                      onChange={(event) => setSanctionId(event.target.value)}
                      required
                    />
                  </Field>
                  <div className="actions">
                    <button className="button secondary" disabled={busy} type="submit">
                      <Sparkles size={17} />
                      Load latest verdict
                    </button>
                  </div>
                </form>
              </>
            )}

            {tab === "sanction" && (
              <>
                <div className="panel-header">
                  <div>
                    <h3>Record sanction</h3>
                    <p>Issuer-only write call. Your wallet must be authorized by the contract.</p>
                  </div>
                </div>
                <form className="grid" onSubmit={handleRecordSanction}>
                  <Field label="Offender address" full>
                    <input
                      placeholder="0x..."
                      value={offender}
                      onChange={(event) => setOffender(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Severity">
                    <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
                      <option value="1">1 - Low</option>
                      <option value="2">2 - Moderate</option>
                      <option value="3">3 - Serious</option>
                      <option value="4">4 - Severe</option>
                      <option value="5">5 - Extreme</option>
                    </select>
                  </Field>
                  <Field label="Sanction timestamp">
                    <input
                      type="number"
                      value={sanctionTimestamp}
                      onChange={(event) => setSanctionTimestamp(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Original evidence URL" full>
                    <input
                      placeholder="https://..."
                      value={evidenceUrl}
                      onChange={(event) => setEvidenceUrl(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Reason" full>
                    <textarea
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                      required
                    />
                  </Field>
                  <div className="actions">
                    <button className="button" disabled={busy} type="submit">
                      {busy ? <Loader2 size={17} /> : <ShieldAlert size={17} />}
                      Record sanction
                    </button>
                  </div>
                </form>
              </>
            )}

            {tab === "petition" && (
              <>
                <div className="panel-header">
                  <div>
                    <h3>Petition redemption</h3>
                    <p>Submit current evidence URLs for GenLayer&apos;s AI Parole Officer review.</p>
                  </div>
                </div>
                <form className="grid" onSubmit={handlePetition}>
                  <Field label="Sanction ID">
                    <input
                      min="1"
                      type="number"
                      value={petitionId}
                      onChange={(event) => setPetitionId(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Petition timestamp">
                    <input
                      type="number"
                      value={petitionTimestamp}
                      onChange={(event) => setPetitionTimestamp(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Chain history URL" full>
                    <input
                      placeholder="https://etherscan.io/address/..."
                      value={chainHistoryUrl}
                      onChange={(event) => setChainHistoryUrl(event.target.value)}
                    />
                  </Field>
                  <Field label="Supporting URLs, one per line" full>
                    <textarea
                      placeholder={"https://example.com/restitution\nhttps://example.com/contributions"}
                      value={supportingUrls}
                      onChange={(event) => setSupportingUrls(event.target.value)}
                      required
                    />
                  </Field>
                  <div className="actions">
                    <button className="button" disabled={busy} type="submit">
                      {busy ? <Loader2 size={17} /> : <Scale size={17} />}
                      File petition
                    </button>
                  </div>
                </form>
              </>
            )}

            {tab === "appeal" && (
              <>
                <div className="panel-header">
                  <div>
                    <h3>Appeal verdict</h3>
                    <p>Issuer-only governance action for challenging an overly lenient verdict.</p>
                  </div>
                </div>
                <form className="grid" onSubmit={handleAppeal}>
                  <Field label="Sanction ID">
                    <input
                      min="1"
                      type="number"
                      value={appealSanctionId}
                      onChange={(event) => setAppealSanctionId(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Appeal timestamp">
                    <input
                      type="number"
                      value={appealTimestamp}
                      onChange={(event) => setAppealTimestamp(event.target.value)}
                      required
                    />
                  </Field>
                  <Field label="Appeal reason" full>
                    <textarea
                      value={appealReason}
                      onChange={(event) => setAppealReason(event.target.value)}
                      required
                    />
                  </Field>
                  <div className="actions">
                    <button className="button" disabled={busy} type="submit">
                      {busy ? <Loader2 size={17} /> : <Gavel size={17} />}
                      Submit appeal
                    </button>
                  </div>
                </form>
              </>
            )}

            <ResultPanel result={result} />
          </div>
        </section>
      </main>
    </div>
  );
}
