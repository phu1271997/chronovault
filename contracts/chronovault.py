# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

json = __import__("json")

DEFAULT_COOLDOWN_SECONDS = 15552000
RECHECK_SECONDS = 7776000
REDEEMED_THRESHOLD = 80
CONDITIONAL_THRESHOLD = 60
DENIED_WITH_PATH_THRESHOLD = 40


def clamp_score(value) -> int:
    try:
        score = int(value)
    except Exception:
        return 0
    if score < 0:
        return 0
    if score > 100:
        return 100
    return score


def address_hex(address: Address) -> str:
    if hasattr(address, "as_hex"):
        return address.as_hex
    return str(address)


def config_int(raw_value: str, default_value: int) -> int:
    try:
        parsed = int(raw_value)
    except Exception:
        return default_value
    if parsed < 0:
        return default_value
    return parsed


def normalize_urls(urls: DynArray[str]):
    normalized = []
    for url in urls:
        text = str(url).strip()
        if text != "":
            normalized.append(text[:500])
    return normalized


def safe_json_loads(raw_value: str):
    try:
        return json.loads(raw_value)
    except Exception:
        return {}


def parse_ai_response(raw_response):
    if isinstance(raw_response, dict):
        return raw_response
    if isinstance(raw_response, str):
        try:
            return json.loads(raw_response)
        except Exception:
            return {
                "behavioral_change_score": 0,
                "restitution_score": 0,
                "consistency_score": 0,
                "severity_discount_score": 0,
                "recidivism_risk_score": 100,
                "final_redemption_score": 0,
                "verdict": "DENIED",
                "specific_evidence_cited": [],
                "required_actions_if_denied_with_path": [
                    "Submit evidence in valid JSON-compatible public sources."
                ],
                "reasoning": f"AI response could not be parsed as JSON: {str(raw_response)[:300]}",
            }
    return {
        "behavioral_change_score": 0,
        "restitution_score": 0,
        "consistency_score": 0,
        "severity_discount_score": 0,
        "recidivism_risk_score": 100,
        "final_redemption_score": 0,
        "verdict": "DENIED",
        "specific_evidence_cited": [],
        "required_actions_if_denied_with_path": [
            "Submit a parseable AI verdict response with concrete public evidence."
        ],
        "reasoning": "AI response had an unsupported shape.",
    }


def recompute_score(ai_data) -> int:
    behavioral = clamp_score(ai_data.get("behavioral_change_score", 0))
    restitution = clamp_score(ai_data.get("restitution_score", 0))
    consistency = clamp_score(ai_data.get("consistency_score", 0))
    severity = clamp_score(ai_data.get("severity_discount_score", 0))
    recidivism = clamp_score(ai_data.get("recidivism_risk_score", 100))
    return (
        behavioral * 30
        + restitution * 25
        + consistency * 25
        + severity * 10
        + (100 - recidivism) * 10
    ) // 100


def verdict_from_score(
    score: int,
    redeemed_threshold: int,
    conditional_threshold: int,
    denied_with_path_threshold: int,
) -> str:
    if score >= redeemed_threshold:
        return "REDEEMED"
    if score >= conditional_threshold:
        return "CONDITIONAL_REDEMPTION"
    if score >= denied_with_path_threshold:
        return "DENIED_WITH_PATH"
    return "DENIED"


def sanction_status_from_verdict(verdict: str) -> str:
    if verdict == "REDEEMED":
        return "REDEEMED"
    if verdict == "CONDITIONAL_REDEMPTION":
        return "CONDITIONAL"
    return "PETITION_DENIED"


def valid_ai_data(data) -> bool:
    if not isinstance(data, dict):
        return False
    required = [
        "behavioral_change_score",
        "restitution_score",
        "consistency_score",
        "severity_discount_score",
        "recidivism_risk_score",
        "reasoning",
    ]
    for key in required:
        if key not in data:
            return False
    return True


class Contract(gl.Contract):
    sanctions: TreeMap[u256, str]
    address_active_sanctions: TreeMap[Address, DynArray[u256]]
    address_redeemed_sanctions: TreeMap[Address, DynArray[u256]]
    total_sanctions: u256
    total_petitions: u256
    vault_config: TreeMap[str, str]
    issuer_authority: TreeMap[Address, bool]

    def __init__(self):
        self.total_sanctions = u256(0)
        self.total_petitions = u256(0)
        self.issuer_authority[gl.message.sender_address] = True
        self.vault_config["default_cooldown_seconds"] = str(DEFAULT_COOLDOWN_SECONDS)
        self.vault_config["conditional_recheck_seconds"] = str(RECHECK_SECONDS)
        self.vault_config["denied_with_path_wait_seconds"] = str(RECHECK_SECONDS)
        self.vault_config["redeemed_threshold"] = str(REDEEMED_THRESHOLD)
        self.vault_config["conditional_threshold"] = str(CONDITIONAL_THRESHOLD)
        self.vault_config["denied_with_path_threshold"] = str(DENIED_WITH_PATH_THRESHOLD)

    def _require_issuer(self):
        sender = gl.message.sender_address
        if not self.issuer_authority.get(sender, False):
            raise gl.vm.UserError("Only authorized issuers may call this method")

    def _get_sanction(self, sanction_id: u256):
        raw = self.sanctions.get(sanction_id, "")
        if raw == "":
            raise gl.vm.UserError("Unknown sanction_id")
        sanction = safe_json_loads(raw)
        if not isinstance(sanction, dict) or "id" not in sanction:
            raise gl.vm.UserError("Stored sanction is malformed")
        return sanction

    def _ids_for_address(self, index_name: str, address: Address):
        try:
            if index_name == "redeemed":
                return self.address_redeemed_sanctions[address]
            return self.address_active_sanctions[address]
        except Exception:
            return []

    def _cooldown_seconds(self) -> int:
        return config_int(
            self.vault_config.get("default_cooldown_seconds", ""),
            DEFAULT_COOLDOWN_SECONDS,
        )

    def _recheck_seconds(self) -> int:
        return config_int(
            self.vault_config.get("conditional_recheck_seconds", ""),
            RECHECK_SECONDS,
        )

    def _denied_with_path_wait_seconds(self) -> int:
        return config_int(
            self.vault_config.get("denied_with_path_wait_seconds", ""),
            RECHECK_SECONDS,
        )

    def _redeemed_threshold(self) -> int:
        return config_int(self.vault_config.get("redeemed_threshold", ""), REDEEMED_THRESHOLD)

    def _conditional_threshold(self) -> int:
        return config_int(
            self.vault_config.get("conditional_threshold", ""),
            CONDITIONAL_THRESHOLD,
        )

    def _denied_with_path_threshold(self) -> int:
        return config_int(
            self.vault_config.get("denied_with_path_threshold", ""),
            DENIED_WITH_PATH_THRESHOLD,
        )

    def _build_review_prompt(
        self,
        sanction,
        supporting_urls_json: str,
        chain_history_url: str,
        original_evidence_text: str,
        supporting_evidence_text: str,
        chain_history_text: str,
        appeal_reason: str,
    ) -> str:
        appeal_section = ""
        if appeal_reason.strip() != "":
            appeal_section = (
                "\nAPPEAL MODE: The issuer claims the prior verdict may have been too lenient. "
                "Apply stricter scrutiny and require stronger evidence before redemption.\n"
                f"Appeal reason: {appeal_reason[:1000]}\n"
            )

        return f"""
You are a skeptical but fair Parole Officer for ChronoVault, an on-chain redemption protocol.

You are not a forgiveness machine. Your job is to protect future victims of recidivism while also recognizing genuine human change. Bias toward DENIAL when evidence is ambiguous because the cost of false redemption is higher than delayed redemption.
{appeal_section}
ORIGINAL SANCTION:
- Sanction id: {sanction.get("id", 0)}
- Offender: {sanction.get("offender", "")}
- Issuer: {sanction.get("issuer", "")}
- Reason: {sanction.get("reason", "")}
- Severity, 1 low to 5 high: {sanction.get("severity", 0)}
- Sanctioned at unix seconds: {sanction.get("sanctioned_at", 0)}
- Original evidence URL: {sanction.get("original_evidence_url", "")}

PETITION EVIDENCE URLS:
{supporting_urls_json}

CHAIN HISTORY HINT URL:
{chain_history_url}

ORIGINAL SANCTION EVIDENCE CONTENT:
{original_evidence_text[:6000]}

SUPPORTING EVIDENCE CONTENT:
{supporting_evidence_text[:10000]}

CHAIN HISTORY CONTENT:
{chain_history_text[:4000]}

Evaluate the petition on exactly five dimensions from 0 to 100:
1. behavioral_change_score: concrete proof of different behavior patterns since the sanction.
2. restitution_score: amends, returned funds, apologies, reparative work, or public accountability.
3. consistency_score: sustained change over time. Penalize panic clean-up behavior right before petitioning.
4. severity_discount_score: proportionality to the original harm. Very severe or irrecoverable harm should score low.
5. recidivism_risk_score: likelihood of repeating the harm. Higher means more risk and hurts redemption.

Rules:
- Cite specific evidence observed in the provided content.
- Reward patterns over isolated events.
- Do not use information that is not visible in the evidence above.
- For DENIED_WITH_PATH, return concrete, verifiable actions, not vague advice.
- Return only raw JSON. Do not include markdown.

Required JSON schema:
{{
  "behavioral_change_score": 0,
  "restitution_score": 0,
  "consistency_score": 0,
  "severity_discount_score": 0,
  "recidivism_risk_score": 0,
  "final_redemption_score": 0,
  "verdict": "REDEEMED",
  "specific_evidence_cited": ["Specific evidence observed"],
  "required_actions_if_denied_with_path": ["Concrete action"],
  "reasoning": "3-5 sentences explaining the verdict"
}}
""".strip()

    @gl.public.view
    def is_issuer(self, address: Address) -> bool:
        return self.issuer_authority.get(address, False)

    @gl.public.write
    def set_issuer_authority(self, issuer: Address, allowed: bool) -> str:
        self._require_issuer()
        self.issuer_authority[issuer] = allowed
        return json.dumps(
            {
                "issuer": address_hex(issuer),
                "allowed": allowed,
                "updated_by": address_hex(gl.message.sender_address),
            },
            sort_keys=True,
        )

    @gl.public.write
    def configure_vault(self, key: str, value: str) -> str:
        self._require_issuer()
        key = key.strip()
        if key == "":
            raise gl.vm.UserError("Config key required")
        self.vault_config[key] = value.strip()
        return json.dumps({"key": key, "value": self.vault_config[key]}, sort_keys=True)

    @gl.public.view
    def get_config(self, key: str) -> str:
        return self.vault_config.get(key, "")

    @gl.public.write
    def record_sanction(
        self,
        offender_address: Address,
        reason: str,
        evidence_url: str,
        severity: u8,
        timestamp: u256,
    ) -> u256:
        self._require_issuer()
        severity_int = int(severity)
        if severity_int < 1 or severity_int > 5:
            raise gl.vm.UserError("Severity must be between 1 and 5")
        if reason.strip() == "":
            raise gl.vm.UserError("Reason required")
        if evidence_url.strip() == "":
            raise gl.vm.UserError("Evidence URL required")

        self.total_sanctions = self.total_sanctions + u256(1)
        sanction_id = self.total_sanctions
        cooldown = self._cooldown_seconds()
        sanctioned_at = int(timestamp)
        sanction = {
            "id": int(sanction_id),
            "offender": address_hex(offender_address),
            "issuer": address_hex(gl.message.sender_address),
            "reason": reason.strip()[:1000],
            "original_evidence_url": evidence_url.strip()[:500],
            "severity": severity_int,
            "sanctioned_at": sanctioned_at,
            "cooldown_seconds": cooldown,
            "status": "ACTIVE",
            "next_eligible_at": sanctioned_at + cooldown,
            "latest_petition_id": 0,
            "redemption_history": [],
        }
        self.sanctions[sanction_id] = json.dumps(sanction, sort_keys=True)
        self.address_active_sanctions[offender_address].append(sanction_id)
        return sanction_id

    @gl.public.write
    def petition_for_redemption(
        self,
        sanction_id: u256,
        supporting_urls: DynArray[str],
        chain_history_url: str,
        petitioned_at: u256,
    ) -> str:
        sanction = self._get_sanction(sanction_id)
        if sanction.get("status", "") in ["REDEEMED", "CONDITIONAL"]:
            raise gl.vm.UserError("Sanction has already received a redemption verdict")
        if int(petitioned_at) < int(sanction.get("next_eligible_at", 0)):
            raise gl.vm.UserError("Cooldown has not elapsed")

        urls = normalize_urls(supporting_urls)
        if len(urls) == 0:
            raise gl.vm.UserError("At least one supporting URL required")
        original_url = str(sanction.get("original_evidence_url", ""))
        chain_url = chain_history_url.strip()[:500]
        urls_json = json.dumps(urls, sort_keys=True)

        def leader_fn():
            try:
                original_evidence = gl.nondet.web.render(original_url, mode="text")
            except Exception:
                original_evidence = "[Unable to render original evidence URL]"

            evidence_parts = []
            for url in urls:
                try:
                    rendered = gl.nondet.web.render(url, mode="text")
                    evidence_parts.append(f"URL: {url}\n{rendered[:4000]}")
                except Exception:
                    evidence_parts.append(f"URL: {url}\n[Unable to render supporting URL]")

            try:
                chain_history = gl.nondet.web.render(chain_url, mode="text") if chain_url != "" else ""
            except Exception:
                chain_history = "[Unable to render chain history URL]"

            prompt = self._build_review_prompt(
                sanction,
                urls_json,
                chain_url,
                original_evidence,
                "\n\n---\n\n".join(evidence_parts),
                chain_history,
                "",
            )
            raw_response = gl.nondet.exec_prompt(prompt, response_format="json")
            return parse_ai_response(raw_response)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            return valid_ai_data(leader_result.calldata)

        ai_data = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        final_score = recompute_score(ai_data)
        verdict = verdict_from_score(
            final_score,
            self._redeemed_threshold(),
            self._conditional_threshold(),
            self._denied_with_path_threshold(),
        )
        next_wait = self._cooldown_seconds()
        if verdict == "CONDITIONAL_REDEMPTION":
            next_wait = self._recheck_seconds()
        if verdict == "DENIED_WITH_PATH":
            next_wait = self._denied_with_path_wait_seconds()
        if verdict == "REDEEMED":
            next_wait = 0

        self.total_petitions = self.total_petitions + u256(1)
        petition_id = self.total_petitions
        next_eligible_at = int(petitioned_at) + next_wait
        petition = {
            "petition_id": int(petition_id),
            "petitioner": address_hex(gl.message.sender_address),
            "supporting_urls": urls,
            "chain_history_url": chain_url,
            "petitioned_at": int(petitioned_at),
            "verdict": verdict,
            "redemption_score": final_score,
            "scores_breakdown": {
                "behavioral_change": clamp_score(ai_data.get("behavioral_change_score", 0)),
                "restitution": clamp_score(ai_data.get("restitution_score", 0)),
                "consistency": clamp_score(ai_data.get("consistency_score", 0)),
                "severity_discount": clamp_score(ai_data.get("severity_discount_score", 0)),
                "recidivism_risk": clamp_score(ai_data.get("recidivism_risk_score", 100)),
            },
            "specific_evidence_cited": ai_data.get("specific_evidence_cited", []),
            "required_actions_if_denied_with_path": ai_data.get(
                "required_actions_if_denied_with_path", []
            ),
            "ai_reasoning": str(ai_data.get("reasoning", ""))[:4000],
            "next_eligible_at": next_eligible_at,
            "appealed": False,
        }

        history = sanction.get("redemption_history", [])
        if not isinstance(history, list):
            history = []
        history.append(petition)
        sanction["redemption_history"] = history
        sanction["latest_petition_id"] = int(petition_id)
        sanction["status"] = sanction_status_from_verdict(verdict)
        sanction["next_eligible_at"] = next_eligible_at
        self.sanctions[sanction_id] = json.dumps(sanction, sort_keys=True)

        offender = Address(str(sanction.get("offender", "")))
        if verdict == "REDEEMED" or verdict == "CONDITIONAL_REDEMPTION":
            self.address_redeemed_sanctions[offender].append(sanction_id)

        return json.dumps(petition, sort_keys=True)

    @gl.public.write
    def appeal_verdict(
        self,
        sanction_id: u256,
        appeal_reason: str,
        appealed_at: u256,
    ) -> str:
        self._require_issuer()
        sanction = self._get_sanction(sanction_id)
        history = sanction.get("redemption_history", [])
        if not isinstance(history, list) or len(history) == 0:
            raise gl.vm.UserError("No petition exists to appeal")
        latest = history[-1]
        if latest.get("verdict", "") not in ["REDEEMED", "CONDITIONAL_REDEMPTION"]:
            raise gl.vm.UserError("Only redemption verdicts may be appealed")
        if bool(latest.get("appealed", False)):
            raise gl.vm.UserError("Latest redemption petition was already appealed")

        original_url = str(sanction.get("original_evidence_url", ""))
        urls = latest.get("supporting_urls", [])
        chain_url = str(latest.get("chain_history_url", ""))
        urls_json = json.dumps(urls, sort_keys=True)

        def leader_fn():
            try:
                original_evidence = gl.nondet.web.render(original_url, mode="text")
            except Exception:
                original_evidence = "[Unable to render original evidence URL]"

            evidence_parts = []
            for url in urls:
                try:
                    rendered = gl.nondet.web.render(str(url), mode="text")
                    evidence_parts.append(f"URL: {url}\n{rendered[:4000]}")
                except Exception:
                    evidence_parts.append(f"URL: {url}\n[Unable to render supporting URL]")

            try:
                chain_history = gl.nondet.web.render(chain_url, mode="text") if chain_url != "" else ""
            except Exception:
                chain_history = "[Unable to render chain history URL]"

            prompt = self._build_review_prompt(
                sanction,
                urls_json,
                chain_url,
                original_evidence,
                "\n\n---\n\n".join(evidence_parts),
                chain_history,
                appeal_reason,
            )
            raw_response = gl.nondet.exec_prompt(prompt, response_format="json")
            return parse_ai_response(raw_response)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            return valid_ai_data(leader_result.calldata)

        ai_data = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        final_score = recompute_score(ai_data)
        verdict = verdict_from_score(
            final_score,
            self._redeemed_threshold(),
            self._conditional_threshold(),
            self._denied_with_path_threshold(),
        )
        next_wait = 0
        if verdict == "DENIED":
            next_wait = self._cooldown_seconds()
        if verdict == "CONDITIONAL_REDEMPTION":
            next_wait = self._recheck_seconds()
        if verdict == "DENIED_WITH_PATH":
            next_wait = self._denied_with_path_wait_seconds()

        latest["appealed"] = True
        latest["appeal_reason"] = appeal_reason.strip()[:1000]
        latest["appealed_at"] = int(appealed_at)
        latest["appeal_result"] = {
            "verdict": verdict,
            "redemption_score": final_score,
            "scores_breakdown": {
                "behavioral_change": clamp_score(ai_data.get("behavioral_change_score", 0)),
                "restitution": clamp_score(ai_data.get("restitution_score", 0)),
                "consistency": clamp_score(ai_data.get("consistency_score", 0)),
                "severity_discount": clamp_score(ai_data.get("severity_discount_score", 0)),
                "recidivism_risk": clamp_score(ai_data.get("recidivism_risk_score", 100)),
            },
            "specific_evidence_cited": ai_data.get("specific_evidence_cited", []),
            "required_actions_if_denied_with_path": ai_data.get(
                "required_actions_if_denied_with_path", []
            ),
            "ai_reasoning": str(ai_data.get("reasoning", ""))[:4000],
            "next_eligible_at": int(appealed_at) + next_wait,
        }
        history[-1] = latest
        sanction["redemption_history"] = history
        sanction["status"] = sanction_status_from_verdict(verdict)
        sanction["next_eligible_at"] = int(appealed_at) + next_wait
        self.sanctions[sanction_id] = json.dumps(sanction, sort_keys=True)
        return json.dumps(latest["appeal_result"], sort_keys=True)

    @gl.public.view
    def get_sanction(self, sanction_id: u256) -> str:
        return self.sanctions.get(sanction_id, "")

    @gl.public.view
    def get_redemption_verdict(self, sanction_id: u256) -> str:
        sanction = self._get_sanction(sanction_id)
        history = sanction.get("redemption_history", [])
        if not isinstance(history, list) or len(history) == 0:
            return ""
        return json.dumps(history[-1], sort_keys=True)

    @gl.public.view
    def check_address_status(self, address: Address) -> str:
        active_ids = self._ids_for_address("active", address)
        redeemed_ids = self._ids_for_address("redeemed", address)
        has_redeemed = False
        has_conditional = False
        for sanction_id in active_ids:
            sanction = safe_json_loads(self.sanctions.get(sanction_id, ""))
            status = sanction.get("status", "")
            if status == "ACTIVE" or status == "PETITION_DENIED":
                return "ACTIVE"
            if status == "CONDITIONAL":
                has_conditional = True
            if status == "REDEEMED":
                has_redeemed = True
        for sanction_id in redeemed_ids:
            sanction = safe_json_loads(self.sanctions.get(sanction_id, ""))
            status = sanction.get("status", "")
            if status == "CONDITIONAL":
                has_conditional = True
            if status == "REDEEMED":
                has_redeemed = True
        if has_conditional:
            return "CONDITIONAL"
        if has_redeemed:
            return "REDEEMED"
        return "NEVER_SANCTIONED"

    @gl.public.view
    def get_sanction_history(self, address: Address) -> str:
        active_ids = self._ids_for_address("active", address)
        redeemed_ids = self._ids_for_address("redeemed", address)
        records = []
        seen = {}
        for sanction_id in active_ids:
            sid = int(sanction_id)
            if sid not in seen:
                seen[sid] = True
                records.append(safe_json_loads(self.sanctions.get(sanction_id, "")))
        for sanction_id in redeemed_ids:
            sid = int(sanction_id)
            if sid not in seen:
                seen[sid] = True
                records.append(safe_json_loads(self.sanctions.get(sanction_id, "")))
        return json.dumps(
            {
                "address": address_hex(address),
                "status": self.check_address_status(address),
                "sanctions": records,
            },
            sort_keys=True,
        )
