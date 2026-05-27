/ Trading calendar function-call template.
/ Production implementations should bind start/end as parameters rather than
/ interpolating unchecked values into q strings.
/ Expected function arguments:
/   start
/   end
/ Expected output: date vector or table/dict with configured date column.

{{ calendar_function }}[start;end]
