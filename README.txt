EARTHSCAPE CLIMATE AGENCY - poora project Python mein (koi HTML file nahi, koi folder nahi)
===========================================================================================

FILES
  app.py               poori website (Streamlit): login, register, dashboard, upload, alerts, support, admin users
  analytics.py         database, data cleaning, forecast, anomaly detection, alert rules
  mapper.py            Hadoop MapReduce - mapper
  reducer.py           Hadoop MapReduce - reducer
  make_sample_data.py  test data banane wali script
  climate_sample.csv   test data (6 stations, 3 saal)
  test_app.py          automatic test
  requirements.txt     libraries

RUN
  pip install -r requirements.txt
  streamlit run app.py --theme.base dark
  Browser khud khulega (http://localhost:8501)

  - "Create account" tab se register karo. PEHLA user ADMIN banta hai.
  - Login ke baad "Data Upload" mein climate_sample.csv upload karo, phir "Dashboard" kholo.
  - MongoDB chal raha ho to wohi use hota hai, warna temporary memory database
    (app band karne par data khatam, browser refresh par dobara login karna parta hai).

ROLES
  admin   = sab kuch + users manage + alert limits badalna
  analyst = data upload + analytics
  viewer  = sirf dekh sakta hai

DATA FORMAT (CSV / JSON)
  date, station, temperature, co2, humidity, rainfall, sea_level, aqi
  Sirf pehle 3 zaroori hain. Missing values khud fill ho jati hain.

HADOOP (har station ka monthly average temperature aur CO2)
  1) Bina Hadoop ke test:
       cat climate_sample.csv | python mapper.py | sort | python reducer.py
  2) Hadoop par (Linux / WSL2):
       hdfs dfs -mkdir -p /earthscape/raw
       hdfs dfs -put -f climate_sample.csv /earthscape/raw/
       hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
         -files mapper.py,reducer.py -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
         -input /earthscape/raw/climate_sample.csv -output /earthscape/processed/monthly_avg
       hdfs dfs -cat /earthscape/processed/monthly_avg/part-00000 | head

TEST
  pytest

SAMAJHNE KA TARTEEB
  1. app.py       - upar se neeche parho: helpers -> login -> dashboard -> upload -> alerts -> support -> users
  2. analytics.py - clean() -> kpis() -> trend() -> anomalies() -> alert rules
