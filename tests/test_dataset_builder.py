from temporalguard.data.dataset_builder import build_dataset


def test_build_dataset_returns_input_copy():
    samples = [{"id": 1}]
    assert build_dataset(samples) == samples
