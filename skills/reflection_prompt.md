# Reflection Prompt

You are evaluating the evidence collected so far in a maintenance investigation.

Look at:

- The original user question.
- All tool calls and results collected so far.

Decide:

1. Is the evidence SUFFICIENT to give a confident answer, PARTIAL, or
   INSUFFICIENT?
2. If it is not sufficient, what specific information is missing?
3. If a next search would help, what exact query and tool should be used?
4. Are sources contradictory? List the conflicts.

Respond with only a JSON object:

```json
{
  "sufficiency": "sufficient | partial | insufficient",
  "missing": "short description or empty string",
  "next_tool": "search_work_orders | search_manuals | web_search | get_work_order | null",
  "next_query": "exact query string or null",
  "conflicts": [
    {
      "between": ["source A", "source B"],
      "issue": "description",
      "preference": "which source to trust and why"
    }
  ],
  "confidence_score": 0.0
}
```

Be strict. Do not mark evidence as sufficient until it covers the core question.
