default = """
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/* parts were cut out as there are unecessary for tinypub to function */

/* blocks */

article,
aside,
details,
div,
dt,
figcaption,
footer,
form,
header,
hgroup,
html,
main,
nav,
section,
summary {
  display: block;
}

body {
  display: block;
  margin-left: 1ex;
}

p, dl, multicol {
  display: block;
  margin-block-start: 1em;
  margin-block-end: 1em;
  text-align: justify;
}

dd {
  display: block;
  margin-inline-start: 40px;
}

blockquote, figure {
  display: block;
  margin-block-start: 2em;
  margin-block-end: 1em;
  margin-inline-start: 2em;
  margin-inline-end: 40px;
}

address {
  display: block;
  font-style: italic;
}

center {
  display: block;
  text-align: center;
}

h1 {
  display: block;
  font-size: 2em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

h2 {
  display: block;
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

h3 {
  display: block;
  font-size: 1.17em;
  font-weight: bold;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

h4 {
  display: block;
  font-size: 1.00em;
  font-weight: bold;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

h5 {
  display: block;
  font-size: 0.83em;
  font-weight: bold;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

h6 {
  display: block;
  font-size: 0.67em;
  font-weight: bold;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

listing {
  display: block;
  margin-block-start: 1em;
  margin-block-end: 1em;
}

xmp, pre, plaintext {
  display: block;
  margin-block-start: 1em;
  margin-block-end: 1em;
}

/* tables */

table {
  display: table;
  border-spacing: 2px;
  border-collapse: separate;
  /* XXXldb do we want this if we're border-collapse:collapse ? */
  box-sizing: border-box;
  text-indent: 0;
}

/* caption inherits from table not table-outer */
caption {
  display: table-caption;
  text-align: center;
}

tr {
  display: table-row;
  vertical-align: inherit;
}

col {
  display: table-column;
}

colgroup {
  display: table-column-group;
}

tbody {
  display: table-row-group;
  vertical-align: middle;
}

thead {
  display: table-header-group;
  vertical-align: middle;
}

tfoot {
  display: table-footer-group;
  vertical-align: middle;
}

/* for XHTML tables without tbody */

td {
  display: table-cell;
  vertical-align: inherit;
  text-align: unset;
  padding: 1px;
}

th {
  display: table-cell;
  vertical-align: inherit;
  font-weight: bold;
  padding: 1px;
}

b, strong {
  font-weight: bolder;
}

i, cite, em, var, dfn {
  font-style: italic;
}

tt, code, kbd, samp {
  font-family: -moz-fixed;
}

u, ins {
  text-decoration: underline;
}

s, strike, del {
  text-decoration: line-through;
}

big {
  font-size: larger;
}

small {
  font-size: smaller;
}

sub {
  vertical-align: sub;
  font-size: smaller;
}

sup {
  vertical-align: super;
  font-size: smaller;
}

nobr {
  white-space: nowrap;
}

mark {
  background: yellow;
  color: black;
}


ul, menu, dir {
  display: block;
  list-style-type: disc;
  margin-block-start: 1em;
  margin-block-end: 1em;
  padding-inline-start: 40px;
}

ul, ol, menu {
  counter-reset: list-item;
  -moz-list-reversed: false;
}

ol {
  display: block;
  list-style-type: decimal;
  margin-block-start: 1em;
  margin-block-end: 1em;
  padding-inline-start: 40px;
}

li {
  display: list-item;
  text-align: match-parent;
}

/* leafs */

/* <hr> noshade and color attributes are handled completely by
 * the nsHTMLHRElement attribute mapping code
 */
hr {
  display: block;
  border: 1px inset;
  margin-block-start: 0.5em;
  margin-block-end: 0.5em;
  margin-inline-start: auto;
  margin-inline-end: auto;
  color: gray;
  -moz-float-edge: margin-box;
  box-sizing: content-box;
}

frameset {
  display: block ! important;
  overflow: -moz-hidden-unscrollable;
  position: static ! important;
  float: none ! important;
  border: none ! important;
}

link {
  display: none;
}

frame {
  border-radius: 0 ! important;
}

iframe {
  border: 2px inset;
}

noframes {
  display: none;
}

spacer {
  position: static ! important;
  float: none ! important;
}

canvas {
  user-select: none;
}

/* hidden elements */
base, basefont, datalist, head, meta, script, style, title,
noembed, param, template {
   display: none;
}

area {
  /* Don't give it frames other than its imageframe */
  display: none ! important;
}
"""
