# Master Specification: Sovereign Autonomous Brain & Service Factory

This document defines the technical constraints and meta-architecture for building an autonomous, multi-node "AI Brain" ecosystem. It bridges the gap between local forensic auditing on Snapdragon hardware and 24/7 remote execution on Oracle Ubuntu cloud instances.

## 1. Physical Infrastructure & Roles
The system follows a strict hierarchy of execution to ensure the system survives weeks of user absence.

### 1.1 The Physical Nodes
- **Remote Engine (Oracle Ubuntu)**: The primary execution environment for 24/7 trading and automation.
- **Diagnostic Terminal (Snapdragon Machine)**: A local node used for "Slow Thinking" audits and backtesting.

### 1.3 Hardware Definition
The local Snapdragon X Elite machine is a Passive Monitor. It serves as a Diagnostic Terminal for forensic audits and local backtesting. It is not an execution node. The cloud instance must never wait for a local signal to perform trade execution or data management.

## 2. Multi-Node Provisioning
The agent uses the following command logic to scale the ecosystem across environments.

### 2.1 Provisioning Logic
The `/provision-service` command includes a mandatory `TargetHost` variable:
- **Default**: `Local_Snapdragon`
- **Options**: `Remote_Oracle_Ubuntu`
If `TargetHost` is set to `Remote`, the agent must automatically generate a deployment script to move the skill and its dependencies to the Ubuntu instance via an automated pipeline.

### 2.6 State Parity Protocol
The agent must maintain logic parity between nodes. When a local "skill" or "workflow" is updated, the orchestrator must trigger a synchronization protocol using SCP or Git with SSH keys. This ensures the remote Oracle host always runs the most recent version of the logic.

## 6. Implementation Checklist
The following verification steps are mandatory before final sign-off:
- [ ] **Windows terminal fix**: Applied `cmd /c` to all local global rules.
- [ ] **State Parity**: Verified that Git push/SCP triggers upon local skill modification.
- [ ] **Headless Stability Test**: Disconnect the local terminal. Verify the remote service continues to process its data queue autonomously for 30 minutes without errors.

## 7. Agentic Governance (Crybtos)
To prevent strategy drift during high volatility, the system integrates a Sovereign "Judge" persona into the execution loop.
- **Kraken Signal Audit**: Every trade signal must be audited by an independent "Auditor" agent before the order is placed.
- **Re-authorization Timer**: No trade remains active for more than 48 hours without a fresh audit and re-authorization from the Auditor agent.

## 8. Infrastructure & Security
- **VPS Localization**: The execution core must reside on a VPS located in Dublin or London to minimize latency to Kraken’s servers.
- **Key Security**: Store all API keys using RSA 2048-bit encryption.
- **Access Control**: Restrict API access to the specific static IP address of the VPS.
- **Feeds**: Use WebSockets for price feeds. Do not use REST polling for high-velocity execution.

## 9. The Risk Bridge
Apply the Sovereign Active Risk formula to all Kraken positions:
- **Adaptive Spreads**: Tighten the Grid or DCA spreads as realized P&L increases.
- **Unrealized Mirror Logic**: Activate a fail-safe to stop the bot immediately if the session drawdown exceeds 3%.

### 9.5 Service Recovery
All Python services on the Oracle instance must be configured as systemd daemons. Every `.service` file in `/etc/systemd/system/` must include these exact directives in the `[Service]` block to ensure survival through transient cloud glitches:
```ini
Restart=always
RestartSec=10
StartLimitIntervalSec=0
```

### 10.1 Remote Verification
The Telegram control service must include a Heartbeat function. It will transmit a "System Healthy" status message to the user every 24 hours at 08:00 UTC. This confirms the engine is running while the user is away for extended periods.
