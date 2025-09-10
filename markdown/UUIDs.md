# Notes on Fixing Iterative Block + Match + Merge + Eval

The BoundaryML (BAML creator) founder says Gemini can't understand long strings like UUIDs, but that it can work with consecutive integers if we create them for our input dataset to BAML before each BamlClient operation, then ETL the UUIDs back afterwards should we need them. I need to eliminate Company.uuid and Company.source_uuids and move to ONLY integer Company.id and Company.source_id in BAML workflows.

1. BAML / Gemini assign a consecutive id integer to each entity in the document,
2. My KG build assigns a new consecutive id integer across all Company records...,
3. I block, match, etc. without UUIDs.,
4. I assign Company.uuid in my code and never submit one to BAML / Gemini.,

Shit, this is going to solve the tracking problem but is a lot of lifting :/ We need to be methodical and create a unit test or some way to verify the schema going into the UDTF for block resizing…
