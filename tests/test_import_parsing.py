from backend.connectors.manual_import import ManualImportConnector


def test_csv_import_parses_common_fields_and_list_columns():
    csv_data = "platform,title,description,deliverables,estimated_minutes,ai_autonomy\nPeoplePerHour,Write script,Need a script,hook|cta,50,0.9\n"
    jobs = ManualImportConnector().parse_csv(csv_data)
    assert len(jobs) == 1
    assert jobs[0].deliverables == ["hook", "cta"]
    assert jobs[0].estimatedMinutes == 50


def test_json_import_accepts_jobs_wrapper():
    jobs = ManualImportConnector().parse_json('{"jobs":[{"platform":"Manual","title":"Task","description":"Details"}]}')
    assert jobs[0].title == "Task"


def test_budget_string_extracts_amount_and_currency():
    job = ManualImportConnector().parse_json('[{"platform":"Upwork","title":"Copy","description":"Provided brief","budget":"35 USD fixed"}]')[0]
    assert job.budgetAmount == 35
    assert job.currency == "USD"
