import os
import fitz

pdf_path = "nlp_lecture_notes.pdf"
doc = fitz.open()

pages_text = [
    """CS224N: Natural Language Processing with Deep Learning
Course Instructors: Prof. Richard Socher, Francois Chaubard, Christopher Manning
Stanford University Department of Computer Science
Lecture 1 Notes - Course Overview & Word Vector Representations

Unit 1: Introduction to Word Vectors & Representation Learning
In traditional natural language processing, words were represented as discrete atomic symbols using one-hot vectors. A one-hot vector is a sparse vector where the vector dimension equals the vocabulary size |V|, containing a 1 at the index of the word and 0 elsewhere.
However, one-hot vectors suffer from the fundamental limitation of orthogonality: the dot product between any two distinct one-hot vectors is zero. Consequently, one-hot representations fail to capture semantic similarity or contextual relationships between words (e.g., 'hotel' and 'motel' are orthogonal in one-hot space).

To overcome this limitation, distributional semantics uses dense continuous word vectors (word embeddings) in R^d, where d is typically 100 to 300 dimensions. Distributional semantics is founded on Firth's distributional hypothesis: 'You shall know a word by the company it keeps.' Words occurring in similar surrounding context windows tend to have similar vector representations.
""",
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Francois Chaubard & Richard Socher - Page 2 of 5

Unit 2: Continuous Bag-of-Words (CBOW) Model Architecture
Word2Vec is a computationally efficient framework introduced by Mikolov et al. for learning word embeddings from large unannotated text corpora. It comprises two primary model architectures: Continuous Bag-of-Words (CBOW) and Continuous Skip-gram.

In the Continuous Bag-of-Words (CBOW) architecture, the model predicts a target center word given a context window of surrounding context words. The input layer averages or sums the input vector representations of all context words within a window size c. The hidden layer multiplies this averaged context vector by a center word weight matrix to compute output scores over the vocabulary, applying a Softmax function to produce a probability distribution for the target center word. CBOW trains faster than Skip-gram and achieves higher accuracy for frequent words.
""",
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Prof. Richard Socher - Page 3 of 5

Unit 3: Continuous Skip-Gram Architecture & Negative Sampling
The Continuous Skip-gram architecture operates inversely to CBOW: given a single center word, the model predicts the surrounding context words within a context window of size c. For each position t in a text corpus, Skip-gram maximizes the log probability of observing context words w_{t+j} given the center word w_t.

Standard Skip-gram uses a full Softmax over the entire vocabulary |V|, which becomes computationally prohibitive for large vocabularies because computing the normalization denominator requires summing over millions of words. To resolve this computational bottleneck, Word2Vec employs Negative Sampling (NEG). Negative Sampling converts the multi-class classification task into a binary logistic regression problem: distinguishing true context words (positive pairs) from k randomly sampled noise words (negative pairs) drawn from a unigram noise distribution raised to the 3/4 power.
""",
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Christopher Manning - Page 4 of 5

Unit 4: Pointwise Mutual Information (PMI) & Matrix Factorization
Before Word2Vec, co-occurrence matrix factorization methods were widely used to learn word representations. A term-context co-occurrence matrix records how frequently words co-occur within a fixed window size across the corpus.

Pointwise Mutual Information (PMI) quantifies the association between a word w and a context word c by measuring the ratio of their joint probability P(w, c) to their marginal probabilities P(w)P(c). Positive PMI (PPMI) replaces negative PMI values with zero to prevent unstable logarithmic estimates for rare pairs. Levy and Goldberg demonstrated that Word2Vec Skip-gram with Negative Sampling is mathematically equivalent to implicitly factorizing a shifted Positive PMI matrix, bridging neural word embeddings with traditional spectral matrix factorization.
""",
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Stanford CS224N - Page 5 of 5

Unit 5: Evaluation & Intrinsic vs Extrinsic Word Vector Benchmarks
Word embedding models are evaluated using two complementary methodologies: intrinsic evaluation and extrinsic evaluation.

Intrinsic evaluation measures word vector quality directly on specific subtasks without integrating vectors into an end-to-end downstream model. Common intrinsic benchmarks include word similarity tasks (measuring Spearman correlation between cosine similarity of word vectors and human similarity ratings, e.g. WordSim-353) and word analogy tasks (solving syntactic and semantic analogies using vector arithmetic, such as king - man + woman = queen). Extrinsic evaluation assesses word vectors by plugging them as input representations into downstream NLP applications, such as named entity recognition (NER), sentiment analysis, or machine translation.
"""
]

for text in pages_text:
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=11)

doc.save(pdf_path)
doc.close()
print(f"Created academic NLP PDF '{pdf_path}' with 5 pages.")
