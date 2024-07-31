import os
import ast
import math
import json
import pandas as pd
from omegaconf import OmegaConf
from tqdm import tqdm
from supabase import create_client

def map_results(df):
    items = []
    for _, row in df.iterrows():
        try:
            items.append({
                'id': row.id,
                'best_rank': row.best_rank,
                'metrics': json.loads(json.dumps(ast.literal_eval(row.metrics))),
                'methodology': row.methodology,
                'uses_additional_data': row.uses_additional_data,
                'paper': row.paper,
                'best_metric': row.best_metric,
                'evaluated_on': row.evaluated_on,
                'evaluation': row.evaluation
            })
        except:
            print('Could nod parse item', row.metrics)

    return items

def upload_chunk(supabase, table, chunk):
    try:
        supabase.table(table).insert(chunk).execute()
    except Exception as exception:
        print('Something went wrong')
        print(exception)
        raise exception
    
def upload_results(cfg, supabase):
    supabase.table('result').delete().not_.is_("id", "null").execute()

    df_results = pd.read_json(f"{cfg.collect.output}/results.json")
    df_results['metrics'] = df_results['metrics'].fillna("{}")
    df_results['best_rank'] = df_results['best_rank'].fillna(-1)

    total = len(df_results)
    page_size = 1000

    for page in tqdm(range(math.ceil(total / page_size))):
        offset = page * page_size
        chunk = df_results.iloc[offset: offset+page_size]
        chunk = map_results(chunk)
        upload_chunk(supabase, 'result', chunk)

def upload() -> None:
    cfg = OmegaConf.load("params.yaml")

    if not os.path.exists(cfg.upload.output):
        os.makedirs(cfg.upload.output)

    url = cfg.upload.supabase_url
    key = cfg.upload.supabase_key
    supabase = create_client(url, key)

    upload_results(cfg, supabase)


    # TODO: Delete All

    # TODO: Upload Areas
    # TODO: Upload Tasks
    # TODO: Upload Evaluations
    # TODO: Upload Results

    return

if __name__ == "__main__":
    upload()