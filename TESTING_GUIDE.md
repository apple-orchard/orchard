# Testing Guide: Chunking & Embedding Pipeline

This guide provides multiple ways to test your upgraded chunking and embedding system with the new `all-mpnet-base-v2` model and optimized chunk sizes.

## 🚀 Quick Start Testing

### Option 1: Comprehensive Test Script
```bash
# Run full test suite
python test_chunking_embeddings.py

# Quick semantic test only
python test_chunking_embeddings.py --quick

# Test with your own file
python test_chunking_embeddings.py --file documents/your_document.txt
```

### Option 2: API Endpoint Tests
```bash
# Start your API first
python main.py  # or docker-compose up

# Then run API tests
python api_test_chunking_embeddings.py

# Test different API endpoint
python api_test_chunking_embeddings.py --url http://localhost:8011
```

## 📊 What Each Test Does

### 1. **Chunking Strategy Test**
- ✅ Tests how your text gets split into chunks
- ✅ Shows chunk sizes, overlap, and distribution
- ✅ Verifies chunk quality and coherence

**Sample Output:**
```
📝 Testing chunking for: Technical Documentation
Original text length: 1234 characters
📊 Results:
  Number of chunks: 3
  Average chunk length: 1456.7
  Min/Max chunk length: 1200/1500
```

### 2. **Embedding Quality Test**
- ✅ Tests how well embeddings capture meaning
- ✅ Shows similarity scores between queries and documents
- ✅ Verifies embedding model performance

**Sample Output:**
```
🧠 Testing embedding quality...
🔍 Query: 'authentication problems'
   Top matches:
     Score: 0.847 - Users are having trouble logging into the system...
     Score: 0.823 - Login failures have been reported by customers...
```

### 3. **Semantic Understanding Test**
- ✅ Tests conceptual similarity (not just keywords)
- ✅ Measures how well the model understands meaning
- ✅ Success rate indicates semantic quality

**Sample Output:**
```
🎯 Testing semantic understanding...
🧪 Test case: 'user authentication problems'
   📊 Top 3 matches (should be relevant):
     1. Score: 0.872 - ✅ Relevant
        Users are having trouble logging into the system
     2. Score: 0.845 - ✅ Relevant
        Login failures have been reported by customers
     3. Score: 0.834 - ✅ Relevant
        The authentication service is experiencing issues

📈 Semantic Understanding Results:
   Tests passed: 3/3
   Success rate: 100.0%
```

### 4. **Full Pipeline Test**
- ✅ Tests complete flow: text → chunks → embeddings → storage → retrieval
- ✅ Measures performance and timing
- ✅ Verifies end-to-end functionality

## 🧪 Interactive Testing Methods

### Method 1: Using the Web Interface
1. Start your application:
   ```bash
   docker-compose up  # or python main.py
   ```
2. Open `http://localhost:3000`
3. Upload a document or paste text
4. Try these test queries:
   - **"authentication issues"** → Should find login problems, access errors
   - **"deployment process"** → Should find CI/CD, release procedures
   - **"performance optimization"** → Should find speed improvements, tuning

### Method 2: Using cURL Commands
```bash
# Test text ingestion
curl -X POST "http://localhost:8011/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text_content": "Our authentication system handles user login and access control...",
    "metadata": {"source": "test_doc"}
  }'

# Test querying
curl -X POST "http://localhost:8011/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does authentication work?",
    "max_chunks": 5
  }'

# Check knowledge base
curl -X GET "http://localhost:8011/knowledge-base/info"
```

### Method 3: Using CLI Tools
```bash
# If you have the CLI set up
./orchard query "authentication problems"
./orchard ingest --text "Sample text content"
./orchard status
```

## 📈 Evaluating Results

### Good Chunking Indicators:
- ✅ **Chunk sizes** around 1500 characters (your target)
- ✅ **Logical breaks** at sentence/paragraph boundaries
- ✅ **Topic coherence** within each chunk
- ✅ **Meaningful overlap** between adjacent chunks

### Good Embedding Indicators:
- ✅ **High similarity scores** (>0.7) for related content
- ✅ **Semantic matching** beyond keywords
- ✅ **Relevant ranking** of results
- ✅ **Low scores** for unrelated content

### Semantic Understanding Success:
- ✅ **80%+ success rate** in semantic tests
- ✅ **Conceptual matches** even with different words
- ✅ **Topic grouping** of related documents
- ✅ **Context awareness** in answers

## 🔍 Advanced Testing Scenarios

### Test Different Document Types:
```bash
# Technical documentation
python test_chunking_embeddings.py --file docs/api_reference.pdf

# Meeting notes
python test_chunking_embeddings.py --file docs/meeting_notes.docx

# User manuals
python test_chunking_embeddings.py --file docs/user_guide.txt
```

### Test Edge Cases:
- **Very short documents** (< 500 characters)
- **Very long documents** (> 50,000 characters)
- **Mixed content** (code + text)
- **Non-English content**
- **Special characters** and formatting

### Performance Testing:
```bash
# Large file ingestion
time python test_chunking_embeddings.py --file large_document.pdf

# Batch query testing
for query in "auth" "deploy" "performance"; do
  curl -X POST "http://localhost:8011/query" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$query problems\"}"
done
```

## 🐛 Troubleshooting Tests

### Common Issues:

1. **"Model not found" error**:
   ```bash
   # Pre-download the model
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"
   ```

2. **API not responding**:
   ```bash
   # Check if API is running
   curl http://localhost:8011/health

   # Check logs
   docker-compose logs api
   ```

3. **Poor semantic scores**:
   - Verify model downloaded correctly
   - Check if using new model settings
   - Run migration script if needed

4. **Chunking issues**:
   - Verify chunk size settings (should be 1500)
   - Check overlap settings (should be 300)
   - Look at chunk preview in test output

## 📊 Comparing Old vs New Performance

### Before Upgrade (MiniLM-L6-v2):
- Chunk size: 1000 characters
- Focus: Keyword matching
- Semantic understanding: ~60-70%

### After Upgrade (MPNet-base-v2):
- Chunk size: 1500 characters
- Focus: Semantic understanding
- Expected semantic understanding: ~85-95%

### Migration Testing:
```bash
# Test old data compatibility
python migrate_embeddings.py  # Migrate existing data
python test_chunking_embeddings.py  # Test new performance
```

## 🎯 Success Criteria

Your chunking and embedding system is working well if:

- ✅ **Chunking**: 2-4 chunks per page, logical breaks, 1400-1500 char average
- ✅ **Embeddings**: >0.8 similarity for related content, <0.3 for unrelated
- ✅ **Semantic**: >85% success rate in understanding tests
- ✅ **Performance**: <2s for ingestion, <1s for queries
- ✅ **API**: All endpoints responding correctly
- ✅ **Quality**: Relevant answers to conceptual questions

## 📚 Example Test Queries

Try these queries to test semantic understanding:

### Authentication & Security:
- "user login problems"
- "access control issues"
- "security verification failing"

### Deployment & DevOps:
- "releasing new features"
- "production rollout process"
- "CI/CD pipeline setup"

### Performance & Optimization:
- "making the app faster"
- "reducing response times"
- "system efficiency improvements"

### User Experience:
- "onboarding new users"
- "getting started guide"
- "account setup process"

Each should find semantically related content even if using different words than what's in your documents!