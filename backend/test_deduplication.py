"""
Test script to demonstrate RAG context deduplication.

This script shows how the _update_knowledge_base method deduplicates
contexts based on filename and chunk_index.
"""

from services.chat import chat_service

# Simulate initial system prompt
system_prompt = """You are strictly bound to reply based on the relevant context. If relevant context is empty, say that you're sorry and you cannot answer this question.

<knowledge_base>
</knowledge_base>"""

# First RAG retrieval (simulated)
first_context = """
================================================================================

[Context 1] Source: tax_guide.pdf (Chunk 5, Relevance Score: 0.8523)
Tax deductions are expenses that can be subtracted from your gross income...

================================================================================

[Context 2] Source: business_expenses.pdf (Chunk 12, Relevance Score: 0.7891)
Business expenses include costs incurred in the ordinary course of business...

================================================================================
"""

# Second RAG retrieval (simulated) - contains one duplicate and one new context
second_context = """
================================================================================

[Context 1] Source: tax_guide.pdf (Chunk 5, Relevance Score: 0.8523)
Tax deductions are expenses that can be subtracted from your gross income...

================================================================================

[Context 2] Source: municipal_taxes.pdf (Chunk 8, Relevance Score: 0.8234)
Municipal taxes or local rates paid for business premises are deductible...

================================================================================
"""

print("=" * 80)
print("DEDUPLICATION TEST")
print("=" * 80)

# First update
print("\n1. Adding first context (2 new contexts):")
updated_prompt_1 = chat_service._update_knowledge_base(system_prompt, first_context)
print(f"   - Added contexts from: tax_guide.pdf (Chunk 5), business_expenses.pdf (Chunk 12)")

# Second update (should only add the new context)
print("\n2. Adding second context (1 duplicate, 1 new):")
updated_prompt_2 = chat_service._update_knowledge_base(updated_prompt_1, second_context)
print(f"   - Skipped duplicate: tax_guide.pdf (Chunk 5)")
print(f"   - Added new context: municipal_taxes.pdf (Chunk 8)")

# Extract and count contexts
kb_start = updated_prompt_2.find("<knowledge_base>")
kb_end = updated_prompt_2.find("</knowledge_base>")
kb_content = updated_prompt_2[kb_start:kb_end + len("</knowledge_base>")]

context_count = kb_content.count("[Context")
print(f"\n3. Final knowledge base contains {context_count} unique contexts")

# Show identifiers
identifiers = chat_service._extract_context_identifiers(kb_content)
print(f"\n4. Unique context identifiers:")
for filename, chunk_idx in sorted(identifiers):
    print(f"   - {filename} (Chunk {chunk_idx})")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
