package main

import (
	"os"
	"text/template"
)

func main() {
	sqlTmpl := `SELECT
{{range $i, $col := .Columns}}{{if $i}}, {{end}}{{$col}}{{end}}
FROM {{.Table}}
WHERE {{range $i, $cond := .Conditions}}{{if $i}} AND {{end}}{{$cond}}{{end}};
`
	tmpl, _ := template.New("sql").Parse(sqlTmpl)

	data := struct {
		Columns    []string
		Table      string
		Conditions []string
	}{
		Columns:    []string{"id", "name", "amount"},
		Table:      "raw_transactions",
		Conditions: []string{"amount > 100", "status = 'completed'"},
	}

	tmpl.Execute(os.Stdout, data)
}
