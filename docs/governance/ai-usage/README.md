# AI usage records after AI-056

`../ai-usage-register.csv` is the historical register (AI-001 to the last ID in that file). Each later
record is **one file here**, named for its ID: `AI-057.csv`, containing one CSV row (no header) in the same nine
columns as the register:

`ID,Date,Student,Tool,Engineering task,AI contribution,Human verification,Decision,Issues found`

Quote fields that contain commas. Why one file per record: two pull requests never edit the same line, so they
cannot conflict. If two pull requests pick the same ID they add the same file name, which git reports, and
`python tools/ai_register.py --check` (run in CI) also fails on a duplicate ID.

- Next unused ID: `python tools/ai_register.py --next`
- Full combined register as CSV: `python tools/ai_register.py`
- Validate (unique IDs, nine columns, file name matches ID): `python tools/ai_register.py --check`

Never edit or delete another person's record. A correction is a new dated record that cites the original ID.
