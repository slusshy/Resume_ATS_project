from app.services.ranking_engine import RankingEngine

print('Creating engine...')
engine = RankingEngine()
print('Loading candidates...')
cands = engine.load_candidates()[:5]
print('Candidates loaded:', len(cands))
print('Running rank_candidates on top 5...')
top = engine.rank_candidates(max_output=5)
print('Top results:')
for item in top:
    print(item.get('candidate_id'), item.get('final_score'))
