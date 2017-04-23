# Gates Foundation IATI processing

Gates Foundation IATI data is available from the [IATI
Registry](https://iatiregistry.org/publisher/bmgf).

The Gates Foundation IATI data uses version 1.03 of the standard.

To run:

```bash
./fetch.sh # fetch external dependencies
./generate_sql.py > out.sql # generate the SQL inserts
```
