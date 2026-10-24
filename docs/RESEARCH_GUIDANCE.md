# Keep research informative

1. **Make comparisons fair.** Before rejecting a model or switching between
   alternatives, check whether each has had enough training for its result to
   be informative. A weak score from an undertrained baseline does not establish
   that the approach is weak.

2. **Give the next experiment a purpose.** Identify the uncertainty it addresses
   and how its result could change your next decision. Prefer experiments that
   help distinguish plausible explanations for the results you have seen.

3. **Notice when tuning becomes a loop.** If repeated small adjustments add
   little useful evidence, step back and reconsider the direction. A different
   model family or hypothesis may be more valuable than another variation of
   the same experiment. Seek a fresh assessment if you cannot tell whether you
   are making progress.

## Basis and status

This is proposed guidance, not a validated improvement. It is inspired by the
[Oh My Quant post's critic examples](https://edotenv.com/blog/oh-my-quant-harness):
an undertrained CNN baseline and repeated learning-rate tuning. The experiment
purpose advice is an inference from those observations.

This guidance is separate from the
[original comparison treatment](../experiments/verifier-context/research-guidance.md).
The [new Sol comparison](experiments/research-judgment-sol/README.md) uses the
heading and three rules above as its additional agent context. This provenance
and status section is not part of that treatment.
