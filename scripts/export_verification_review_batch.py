import json

def export_candidates():
    input_file = "data/benchmark/verification/candidates.jsonl"
    output_file = "data/benchmark/verification/review_batch.md"
    
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Verification Candidates Review Batch\n\n")
        for idx, line in enumerate(lines):
            data = json.loads(line)
            f.write(f"## Candidate {idx + 1}: {data['claim_id']}\n")
            f.write(f"- **Claim Text**: {data['claim_text']}\n")
            f.write(f"- **Source Notice ID**: {data['source_notice_id']} (Version {data['source_version_id']})\n")
            f.write(f"- **Mutation Type**: {data.get('mutation_type', 'None')}\n")
            f.write(f"- **Expected Trust State**: {data['expected_trust_state']}\n")
            f.write(f"- **Synthetic Flag**: {data['is_synthetic']}\n")
            f.write(f"- **Review Status**: {data['review_status']}\n")
            f.write("---\n")
            
    print(f"Exported {len(lines)} candidates to {output_file}")

if __name__ == "__main__":
    export_candidates()
