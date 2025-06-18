class BaseRankingModel:
    def rank(self, inputs):
        raise NotImplementedError("Subclasses should implement this method")

    async def async_rank(self, query: str, passages: list[str]):
        if len(passages) == 0:
            return []
        inputs = {
            'source_sentence': [query],
            'sentences_to_compare': passages
        }

        ranked_passages = sorted(
            [(passage, float(score)) for passage, score in
             zip(passages, self.rank(inputs).get("scores", []), strict=False)],
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked_passages
