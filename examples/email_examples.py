"""
Example of an email alert for demonstration purposes.
"""

# Example 1: CRITICAL Mandatory Upgrade
EXAMPLE_CRITICAL = """
Subject: 🚨 CRITICAL [MANDATORY] ethereum/go-ethereum Update: v1.13.0

Blockchain Release Monitor Alert
============================================================

Repository: ethereum/go-ethereum
Version Change: v1.12.2 → v1.13.0
Severity: CRITICAL
Mandatory Upgrade: YES

============================================================
SUMMARY
============================================================

This release contains a critical security patch for a consensus
vulnerability discovered in the block validation logic. Additionally,
a hard fork is scheduled for block 18500000 (approximately October 15,
2024). All nodes must upgrade before this block to avoid chain split.

============================================================
REASONING
============================================================

The consensus vulnerability (CVE-2024-XXXX) could allow malicious
actors to create invalid blocks that older versions would accept,
potentially causing a chain split. The hard fork includes protocol
changes that make this version incompatible with older versions after
activation. Network will reject connections from nodes running older
versions after the fork.

============================================================
RECOMMENDATION
============================================================

⚠️  This is a MANDATORY upgrade. Action required:
   - Review the changes immediately
   - Plan upgrade timeline
   - Test in staging environment
   - Deploy to production ASAP

============================================================
LINKS
============================================================

Repository: https://github.com/ethereum/go-ethereum
New Version: https://github.com/ethereum/go-ethereum/releases/tag/v1.13.0

============================================================

Generated at: 2024-10-01 14:30:00 UTC
Blockchain Release Monitor
"""


# Example 2: HIGH Priority Update
EXAMPLE_HIGH = """
Subject: ⚠️ HIGH cosmos/cosmos-sdk Update: v0.47.5

Blockchain Release Monitor Alert
============================================================

Repository: cosmos/cosmos-sdk
Version Change: v0.47.4 → v0.47.5
Severity: HIGH
Mandatory Upgrade: NO

============================================================
SUMMARY
============================================================

This release fixes several important bugs in the staking module
and improves consensus performance. Includes a fix for a memory
leak that could cause validator nodes to crash under high load.

============================================================
REASONING
============================================================

While not a mandatory upgrade, this version addresses stability
issues that affect validator operations. The memory leak fix is
particularly important for validators processing high transaction
volumes. Performance improvements in consensus could reduce block
times by 5-10%.

============================================================
RECOMMENDATION
============================================================

⚠️  HIGH priority update:
   - Review changes at your earliest convenience
   - Plan upgrade within reasonable timeframe
   - Consider impact on your infrastructure

============================================================
LINKS
============================================================

Repository: https://github.com/cosmos/cosmos-sdk
New Version: https://github.com/cosmos/cosmos-sdk/releases/tag/v0.47.5

============================================================

Generated at: 2024-10-01 14:30:00 UTC
Blockchain Release Monitor
"""


# Example 3: Tag-Only Repository (No Release Notes)
EXAMPLE_TAG_ONLY = """
Subject: 🚨 CRITICAL [MANDATORY] bitcoin/bitcoin Update: v26.0

Blockchain Release Monitor Alert
============================================================

Repository: bitcoin/bitcoin
Version Change: v25.1 → v26.0
Severity: CRITICAL
Mandatory Upgrade: YES

============================================================
SUMMARY
============================================================

Major consensus update with security fixes and protocol improvements.
Multiple commits address memory management issues and improve node
synchronization. Includes changes to transaction validation that
could affect consensus.

============================================================
REASONING
============================================================

Analysis of commit messages between v25.1 and v26.0 reveals multiple
security-related fixes including buffer overflow prevention and
improved validation of peer messages. Several commits reference
"consensus" and "validation" indicating protocol-level changes that
may require upgrade for network compatibility.

============================================================
RECOMMENDATION
============================================================

⚠️  This is a MANDATORY upgrade. Action required:
   - Review the changes immediately
   - Plan upgrade timeline
   - Test in staging environment
   - Deploy to production ASAP

============================================================
LINKS
============================================================

Repository: https://github.com/bitcoin/bitcoin
New Version: https://github.com/bitcoin/bitcoin/releases/tag/v26.0

============================================================

Generated at: 2024-10-01 14:30:00 UTC
Blockchain Release Monitor
"""


# Example 4: Test Email
EXAMPLE_TEST = """
Subject: Blockchain Release Monitor - Test Email

This is a test email from Blockchain Release Monitor.

If you received this email, your email configuration is working correctly.

Configuration:
- SMTP Host: smtp.gmail.com
- SMTP Port: 587
- From: blockchain-monitor@example.com
- To: admin@example.com

Generated at: 2024-10-01 14:30:00 UTC
"""


if __name__ == "__main__":
    print("Email Alert Examples")
    print("=" * 60)
    print("\n1. CRITICAL Mandatory Upgrade:")
    print(EXAMPLE_CRITICAL)
    print("\n2. HIGH Priority Update:")
    print(EXAMPLE_HIGH)
    print("\n3. Tag-Only Repository:")
    print(EXAMPLE_TAG_ONLY)
    print("\n4. Test Email:")
    print(EXAMPLE_TEST)
