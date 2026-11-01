const REPLACEMENTS: Array<[string, string]> = [
  ['Bevoelkerungsentwicklung', 'Bevölkerungsentwicklung'],
  ['Bevoelkerung', 'Bevölkerung'],
  ['bevoelkerung', 'bevölkerung'],
  ['Auslaendische', 'Ausländische'],
  ['auslaendischen', 'ausländischen'],
  ['auslaendische', 'ausländische'],
  ['Auslaender', 'Ausländer'],
  ['auslaender', 'ausländer'],
  ['Zuzuege', 'Zuzüge'],
  ['Fortzuege', 'Fortzüge'],
  ['Veraenderung', 'Veränderung'],
  ['Ausgewaehlt', 'Ausgewählt'],
  ['ausgewaehlt', 'ausgewählt'],
  ['ausfuehren', 'ausführen'],
  ['Fuehre', 'Führe'],
  ['pruefen', 'prüfen'],
  ['oeffentlichen', 'öffentlichen'],
  ['oeffentliche', 'öffentliche'],
  ['regelmaessig', 'regelmäßig'],
  ['geschuetzt', 'geschützt'],
  ['laedt', 'lädt'],
  ['koennen', 'können'],
  ['Ueber', 'Über'],
  ['ueber', 'über'],
  ['fuer', 'für'],
]

export function displayText(value: string): string {
  return REPLACEMENTS.reduce((text, [from, to]) => text.replaceAll(from, to), value)
}
