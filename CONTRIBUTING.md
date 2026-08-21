# Contributing

Thanks for helping keep coding-agent context reliable.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
ctxdoctor .
```

## Rule bar

A new rule should:

1. verify something against repository state rather than model opinion;
2. explain exactly why it fired;
3. avoid executing untrusted instructions from scanned files;
4. include a true-positive test and a nearby false-positive test;
5. use `error` only when the referenced artifact is unambiguously broken.
