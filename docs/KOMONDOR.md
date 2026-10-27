# Komondor connection

Always check for and reuse an existing authenticated SSH connection before
starting a fresh login or requesting eduID approval. The gateway is transit-only;
its [no-modification rule](../AGENTS.md#protected-infrastructure-greengoblin) still applies.

Connect to the existing gateway account using its known address and host key.
On the gateway, inspect `ssh -G <cluster-alias>` for the configured username and
`controlpath`, then check that exact existing socket:

```sh
ssh -S <existing-control-path> -O check <cluster-alias>
```

If the master is alive, reuse it with fresh-connection fallback disabled:

```sh
ssh -T -S <existing-control-path> -o ControlMaster=no \
  -o BatchMode=yes -o ProxyCommand=false -o StrictHostKeyChecking=yes \
  -o UpdateHostKeys=no -o PermitLocalCommand=no <cluster-alias> 'id -un; hostname'
```

Verify the resulting cluster identity and project permissions before submitting
work. Different aliases may represent different project accounts; an available
socket is not interchangeable with another identity. Never stop another user's
master connection or jobs. Do not create sockets, change configuration, or update
known-hosts files on the gateway. Apply the same no-write SSH settings to the
outer gateway connection, with `ControlPath=none` when no local master is used.

If no suitable master exists, use a fresh approved SSH login and its eduID flow.
Keep that session alive for the work; batch jobs continue independently after
submission. Connection reuse reduces repeated prompts but does not guarantee
permanent access or remove authentication requirements.

Verified on 27 October 2026: an existing gateway master reached Komondor without
another eduID prompt, and the experiment directory was readable. Access and
resource allocations must still be checked when resuming work.
