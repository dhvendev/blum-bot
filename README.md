# BlumBot

This bot can collect a daily reward, can launch farming and collect it, and burn game passes. A session registration system with connection proxy.





## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_ID=1234567` - Your info in tg_app

`API_HASH=absd` - Your info in tg_app

`REF=ref_ABCD` - Your ref param

`CLAIM_FARMING=1` - Claim farming or not (1 / 0)

`NIGHT_SLEEP=1` - Sleep night or not (1 / 0)

`MIN_USE_PASSES=5` - Min count burn pass

`MAX_USE_PASSES=9` - Max count burn pass


## Installation and run

📌 I tested this project in 3.10.13 version

☄️ Install this project

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 main.py
```
    