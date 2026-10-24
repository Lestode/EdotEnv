# Documentation rules

- Keep supporting project documentation in `docs/`; keep `AGENTS.md` at the project root.
- Keep project documents logically consistent, both internally and with each other.
- Give each topic one authoritative home and link to it from other documents instead of repeating it. Keep scope, decisions, assumptions, and open/deferred questions in `AGENTS.md`; implementation tasks in `docs/TODO.md`; and topic-specific findings in the relevant supporting document.
- Keep TODO items actionable. Translate requirements into concrete implementation or validation work without copying requirement lists, decision registers, or checklists maintained elsewhere.
- Distinguish confirmed decisions, tentative assumptions, open questions, and deferred decisions.
- Move answered questions into confirmed decisions and update affected documents; do not leave resolved questions open.
- Use agreed decisions and the reference paper to resolve settled details instead of asking again.
- Always bring conflicting information to the user for review before choosing a resolution, even when a new request introduces the conflict or an existing decision suggests a correction. Name the affected sources, explain the consequences, and propose a correction under the [finding-resolution and conflict policy](WORKFLOW.md#finding-resolution-and-conflicts). Flag ambiguities and other issues; ask for clarification when existing decisions do not resolve them.
- When data, instructions, or execution conditions affect an agent's decisions or outcomes, normally make the relevant facts and constraints visible to that agent. This includes information needed to interpret the data, plan within available budgets, and understand the submission requirements. Document intentional withholding and its experimental purpose; preserve teacher-only context and hidden evaluation data boundaries.
- Check what the agent actually receives against what execution enforces. Operator documentation or configuration alone does not establish agent awareness. Flag mismatches, such as an instruction promising more time than the runner allows, and identify unverified visibility when the actual prompts or runtime evidence are unavailable.
