#!/usr/bin/python3
import glob
import subprocess
import argparse
import os
import sqlite3

def calcRates():
    update = """update imc set page_empty = ?, page_conflict = ?, page_hit = ?  
    where socket = ? and time = ?"""
    select = """select socket,time,
    (cast(act_count as float) - pre_count_page_miss) / (cas_count_rd + cas_count_wr) as "page_empty"
    ,(cast(pre_count_page_miss as float)) / (cas_count_rd + cas_count_wr) as "page_conflict"
    ,1 - (cast(act_count as float) - pre_count_page_miss) / (cas_count_rd + cas_count_wr) - cast(pre_count_page_miss as float) / (cas_count_rd + cas_count_wr) as "page_hit"
    from imc"""
    con = sqlite3.connect(output)
    con.execute("alter table imc add column page_empty real")
    con.execute("alter table imc add column page_conflict real")
    con.execute("alter table imc add column page_hit real")
    cur = con.cursor()
    cur.execute(select)
    data = cur.fetchall()
    for row in data:
        socket = row[0]
        time = row[1]
        pageEmpty = row[2]
        pageConflict = row[3]
        pageHit = row[4]
        cur.execute(update,(pageEmpty,pageConflict,pageHit,socket,time))
    con.commit()
    con.close()

parser = argparse.ArgumentParser()
parser.add_argument("--output","-o",default="perf.db")
parser.add_argument("--csv",action="store_true",default=False)
parser.add_argument("command",nargs=argparse.REMAINDER)
args = parser.parse_args()
output = args.output;
outputTemp = args.output + ".csv"

# asterisk in event names not supported in older perf versions
eventString="uncore_imc_*/event=0x01,umask=0x03,name=\'act_count\'/,"
eventString+="uncore_imc_*/event=0x04,umask=0x03,name=\'cas_count.rd\'/,"
eventString+="uncore_imc_*/event=0x04,umask=0x0C,name=\'cas_count.wr\'/,"
eventString+="uncore_imc_*/event=0x02,umask=0x01,name=\'pre_count.page_miss\'/"

perf = "~/bin/perf"
command = " ".join(args.command)
perfOptions =  " stat --no-big-num --per-socket -I 500 -x , -o %s -e %s %s" % (outputTemp,eventString,command)

subprocess.call(perf + perfOptions,shell=True)

txt2sqlExe = os.path.dirname(os.path.abspath(__file__)) + "/graphem/a2sql/bin/txt2sql"
txt2sql= txt2sqlExe + """ "%s" --table imc \
	--exp '(?P<time>\d+\.\d+),S(?P<socket>\d),1,(?P<act_count>\d+),,act_count' \
	--exp '(?P<time>\d+\.\d+),S(?P<socket>\d),1,(?P<cas_count_rd>\d+),,cas_count\.rd' \
	--exp '(?P<time>\d+\.\d+),S(?P<socket>\d),1,(?P<cas_count_wr>\d+),,cas_count\.wr' \
	--row '(?P<time>\d+\.\d+),S(?P<socket>\d),1,(?P<pre_count_page_miss>\d+),,pre_count\.page_miss' \
    "%s"
    """ % (output,outputTemp)

if not args.csv:
    if os.path.exists(output):
        os.remove(output)
    subprocess.call(txt2sql,shell=True)
    os.remove(outputTemp)
else:
    os.rename(outputTemp,output)

calcRates();