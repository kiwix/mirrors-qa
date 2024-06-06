from mirrors_qa_worker.manager.worker import WorkerManager


def main():
    WorkerManager(worker_id="").run()
