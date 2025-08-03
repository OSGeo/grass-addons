<h2>DESCRIPTION</h2>

<em>v.greedycolors</em> assigns numbers to areas such that no two
adjacent areas have the same number. At the same time, it tries to use
as few numbers as possible. The numbers are stored in the attribute table,
by default in the column &quot;greedyclr&quot; which is created if not
existing. These numbers can then be used to assign RGB colors in a new
column to be used with e.g. <em>d.vect</em> .

<p>
<em>v.greedycolors</em> works best if areas have unique categories. If
multiple areas have the same category, the corresponding network of
neighboring areas can become fairly complex, resulting in a larger
number of greedy colors. If the purpose is to assign different colors to
neighboring areas, irrespective of their category values, unique
category values need to be assigned first, e.g. to a new layer with
<em><a href="v.category">v.category</a></em>.

<p>
There is always at least one optimal solution for greedy colors, using
as few colors as possible. However, it is usually computationally
intensive and not practical to search for an optimal solution. Therefore
a good solution is aproximated by ordering the areas first, before
assigning greedy colors. Here, the areas with the least neighbors are
processed first.

<h2>EXAMPLE</h2>
Assigning greedy colors to county boundaries in the North Carolina
sample dataset:

<p>
Make a copy of the data:
<div class="code"><pre>
g.copy vect=boundary_county,my_boundary_county
</pre></div>

Greedy colors
<div class="code"><pre>
v.greedycolors map=my_boundary_county
</pre></div>

Check number and frequency of greedy colors
<div class="code"><pre>
db.select sql="select greedyclr,count(greedyclr) from my_boundary_county group by greedyclr"
</pre></div>
gives
<div class="code"><pre>
greedyclr|count(greedyclr)
1|262
2|351
3|302
4|11
</pre></div>
four different colors were needed such that no two adjacent areas have
the same color

<p>
Assign RGB colors:
<div class="code"><pre>
v.db.addcolumn map=my_boundary_county column="GRASSRGB varchar(11)"

v.db.update map=my_boundary_county column=GRASSRGB value="127:201:127" where="greedyclr = 1"
v.db.update map=my_boundary_county column=GRASSRGB value="190:174:212" where="greedyclr = 2"
v.db.update map=my_boundary_county column=GRASSRGB value="253:192:134" where="greedyclr = 3"
v.db.update map=my_boundary_county column=GRASSRGB value="255:255:153" where="greedyclr = 4"
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="v.colors.html">v.colors</a>,
<a href="v.category.html">v.category</a>
</em>

<h2>AUTHOR</h2>

Markus Metz, mundialis, Germany
