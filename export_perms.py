import csv
from collections import defaultdict
order_map={1:"HFB",2:"HBF",3:"FHB",4:"FBH",5:"BHF",6:"BFH"}

gw=defaultdict(dict)
with open("results/perms_all.csv",encoding="utf-8") as f:
    r=csv.DictReader(f)
    for row in r:
        if row.get("type")!="scalar": continue
        if row.get("module")!="LightIoTNetwork.gateway": continue
        try: val=float(row["value"])
        except: continue
        gw[row["run"]][row["name"]]=val

rows=[]
for run,m in gw.items():
    sid=int(m.get("stageOrderId",0))
    ords=order_map.get(sid,"")
    acc=m.get("totalAccepted",0.0)
    dH=m.get("totalDroppedHmac",0.0)
    dF=m.get("totalDroppedReplay",0.0)
    dB=m.get("totalDroppedDup",0.0)
    total=acc+dH+dF+dB
    pct=lambda x: round(100*x/total,2) if total>0 else 0.0
    rows.append({
      "کانفیگ": run.split("-")[0],
      "ترتیب": ords,
      "کار متوسط": round(m.get("workAvg_units",0.0),3),
      "انرژی به ازای پیام معتبر (میلی‌ژول)": round(m.get("energyPerMsg_mJ",0.0),3),
      "حذف در H درصد": pct(dH),
      "حذف در F درصد": pct(dF),
      "حذف در B درصد": pct(dB),
      "مشاهده کوتاه": ("ok" if total>0 else "بدون ورودی معتبر")
    })

rank={"HFB":1,"HBF":2,"FHB":3,"FBH":4,"BHF":5,"BFH":6}
rows.sort(key=lambda r:(r["کانفیگ"],rank.get(r["ترتیب"],99)))

hdr=["کانفیگ","ترتیب","کار متوسط","انرژی به ازای پیام معتبر (میلی‌ژول)","حذف در H درصد","حذف در F درصد","حذف در B درصد","مشاهده کوتاه"]
with open("results/table_3_7_permutations.csv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=hdr); w.writeheader(); w.writerows(rows)
print("Wrote results/table_3_7_permutations.csv ; rows:",len(rows))
