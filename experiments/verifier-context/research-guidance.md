# Checking your research findings

Use the public data to check whether you found a useful pattern or just got
lucky. All validation periods below come from the public data; the hidden
evaluation data remains separate.

## Choose where you will test before seeing the scores

Decide your training and validation periods in advance. Do not keep changing
the validation period until the model looks good. Testing ten different months
and reporting only the best month gives a misleading picture.

## Lots of rows do not guarantee strong evidence

Check whether your model works across several periods. Do not assume a result
is reliable just because the dataset contains millions of rows. Nearby minutes
may be similar, and different instruments may move together, so the rows are
not necessarily independent pieces of evidence.

## Check whether complicated ideas beat a simple approach

Start with a simple model. When you add something, check whether it improves
the task's weighted correlation score on the same validation data. Otherwise,
you might build something complicated without knowing whether the extra work
helped.

## Save some public data for one final check

Use one period to develop your ideas. Keep another, later public period
untouched until you have chosen your final model. Then check whether it still
works. After repeatedly looking at the same validation results, you can learn
what works on that particular period without finding something that works
elsewhere. If the final check disappoints, report that result too.
