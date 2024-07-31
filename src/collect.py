import os
import json
from omegaconf import OmegaConf
from pathlib import Path
from tqdm import tqdm
from paperswithcode import PapersWithCodeClient

def map_area_results(areas):
    return list(map(lambda x: {
            'id': x.id,
            'name': x.name
        }, areas))

def map_task_results(area_id, results):
    return list(map(lambda x: {
            'id': x.id,
            'area': area_id,
            'name': x.name,
            'description': x.description
        }, results))

def map_evaluation_results(results):
    return list(map(lambda x: {
            'id': x.id,
            'task': x.task,
            'dataset': x.dataset,
            'description': x.description
        }, results))

def map_results(results, evaluation):
    return list(map(lambda x: {
            'id': x.id,
            'best_rank': x.best_rank,
            'metrics': x.metrics,
            'methodology': x.methodology,
            'uses_additional_data': x.uses_additional_data,
            'paper': x.paper,
            'best_metric': x.best_metric,
            'evaluated_on': x.evaluated_on,
            'evaluation': getattr(x, 'evaluation', evaluation['id'])
        }, results))

def get_all_pages(request_method, map_results):
    all_elements = []

    retry_count = 0
    max_retry = 3
    page = 1
    iterms_per_page = 100

    while True:
        try:
            response = request_method(page, iterms_per_page)
            results = map_results(response.results)
            all_elements.extend(results)

            page += 1
            if response.next_page == None:
                break
            retry_count = 0
        except:
            if retry_count >= max_retry:
                raise Exception("Max retry exceeded")
            print(f'Failed to retreive page, retrying {retry_count}/{max_retry}')
            retry_count += 1

    return all_elements


def save_as_json(cfg, file_name, obj):
    output_path = Path(f"{cfg.collect.output}/{file_name}.json")
    output_path.open("w", encoding="utf-8").write(json.dumps(obj, indent=2))


def collect() -> None:
    cfg = OmegaConf.load("params.yaml")

    if not os.path.exists(cfg.collect.output):
        os.makedirs(cfg.collect.output)

    client = PapersWithCodeClient(token=cfg.collect.paperswithcode_token)

    areas = get_all_pages(
        lambda page, items_per_page: client.area_list(page=page, items_per_page=items_per_page),
        map_area_results
    )
    save_as_json(cfg, 'areas', areas)

    all_tasks = []
    for area in tqdm(areas):
        tasks = get_all_pages(
            lambda page, items_per_page: client.area_task_list(area_id=area['id'], page=page, items_per_page=items_per_page),
            lambda task: map_task_results(area['id'], task)
        )
        all_tasks.extend(tasks)
    save_as_json(cfg, 'tasks', all_tasks)

    tasks = get_all_pages(
        lambda page, items_per_page: client.task_list(page=page, items_per_page=items_per_page),
        map_task_results
    )
    save_as_json(cfg, 'tasks', tasks)

    all_evaluations = []
    for task in tqdm(tasks):
        evaluations = get_all_pages(
            lambda page, items_per_page: client.task_evaluation_list(task['id'], page=page, items_per_page=items_per_page),
            map_evaluation_results   
        )
        all_evaluations.extend(evaluations)
    save_as_json(cfg, 'evaluations', all_evaluations)

    all_results = []
    for evaluation in tqdm(all_evaluations):
        results = get_all_pages(
            lambda page, items_per_page: client.evaluation_result_list(evaluation['id'], page=page, items_per_page=items_per_page),
            lambda result: map_results(result, evaluation)
        )
        all_results.extend(results)

    save_as_json(cfg, 'results', all_results)
    return

if __name__ == "__main__":
    collect()