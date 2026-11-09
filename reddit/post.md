**Title:** [OC] Does Parliament notice disasters? Commons speeches naming the place jump to 10x their usual level in the month of a UK disaster, then mostly fade within the year (64 disasters, 1910 to 2020)

**Body:**

I counted, month by month, the House of Commons speeches that named the place of 64 UK disasters between 1910 and 2020 (pit explosions, rail and air crashes, fires, crowd crushes, bombings and shootings; 4,346 deaths), from two years before to five years after.

- In the month of a disaster, speeches naming the place rise to 10.4x their usual level. Nothing builds up beforehand.
- Half of the extra attention over five years comes within a median of 8.5 months. A few disasters followed by public inquiries, such as Grenfell Tower and Piper Alpha, held attention for years.
- The death toll explains little: the raw rank correlation is -0.06. In my planned model twice the deaths goes with about 33% more attention, and even that is not robust.
- London and the South East seem to get more attention, but that rests on two disasters (Grenfell Tower and the King's Cross fire).
- Later I found search words for 22 more disasters and added them under the same rules. With all 86, twice the deaths goes with about 44% more attention: a bit clearer, still not robust.
- Any list of disasters is a list of what is remembered, and the words matter: "in Lockerbie" turns up 10 times in five years, "Lockerbie" 239.

Interactive map with a month-by-month chart for each disaster: https://maps.tristanhotham.com/disaster-attention/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia list of disasters in Great Britain and Ireland by death toll (CC BY-SA); Wikidata (CC0); ONS boundaries. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/disaster-attention
