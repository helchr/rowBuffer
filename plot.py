#!/usr/bin/python

import sys
import lots_plots as lp 
g = lp.lots_plots()

db = str(sys.argv[1])
outList = db.split(".")[:-1]
out = ".".join(outList)

sockets=g.do_sql(db,"select distinct socket from imc order by socket",single_col=1)
metrics=["page_hit","page_empty","page_conflict"]

def plotRatesByTime():
    query="""
    select time, "{metric}"*100 from imc where socket = {socket}
    """

    g.default_terminal = """pdf noenhanced font ',14' size 6,3"""
    g.graphs((db, query),
    graph_attr="""set key right top outside samplen 3 width -1
    set ylabel offset 1.5,0,0
    set xlabel offset 0,0.5,0
    set title offset 0,-0.5,0
    set yrange [0:100]
    set style line 1 linecolor rgb 'green' 
    set style line 2 linecolor rgb 'blue' 
    set style line 3 linecolor rgb 'red' 
    set style increment user
    """,
    output=out+"-socket{socket}.pdf",
    plot_with="linespoints",
    using="1:2",
    graph_title="Row Buffer on Socket {socket}",
    plot_title="{metric}",
    xlabel="Time (s)",
    ylabel="Percent",
    metric=metrics,
    socket=sockets,
    graph_vars=["socket"])

plotRatesByTime()

