import os
import fitz

pdf_path = "nlp_academic_lecture_14p.pdf"
doc = fitz.open()

sections_text = [
    # Page 1
    """CS224N: Natural Language Processing with Deep Learning
Course Instructors: Prof. Richard Socher, Francois Chaubard, Christopher Manning
Stanford University Department of Computer Science
Lecture 1 Notes - Introduction to Natural Language Processing & Word Vectors

Unit 1: Introduction to Natural Language Processing & Semantic Representations
Natural language processing (NLP) is an interdisciplinary subfield of computer science, artificial intelligence, and computational linguistics concerned with enabling computers to understand, interpret, and generate human languages.
Historically, early NLP systems relied on symbolic rules and discrete representation of words as atomic symbols. Discrete representations map each word in a vocabulary V to a unique sparse one-hot vector in R^{|V|}, where the vector entry corresponding to the target word index is 1 and all other entries are 0.
""",
    # Page 2
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Francois Chaubard & Richard Socher - Page 2 of 14

Unit 2: Limitations of One-Hot Vectors & The Orthogonality Problem
While one-hot representation provides a straightforward structural encoding for words, it exhibits severe fundamental limitations when representing semantic relationships.
In a one-hot vector space, every word vector is orthogonal to every other word vector. Consequently, the dot product between any two distinct one-hot vectors is identically zero: v_w1 . v_w2 = 0.
Because orthogonal vectors share no inner-product similarity, one-hot encodings cannot represent word similarity or semantic closeness (e.g., 'hotel' and 'motel' share no more vector overlap than 'hotel' and 'cat'). Furthermore, vector dimensionality scales linearly with vocabulary size |V|, causing extreme memory sparsity.
""",
    # Page 3
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 3 of 14

Unit 3: Distributional Semantics & Firth's Distributional Hypothesis
To address the orthogonality limitation of discrete representations, modern NLP relies on distributional semantics. Distributional semantics represents words as dense continuous vectors in R^d, where d is typically 100 to 300 dimensions.
Distributional semantics is founded on J.R. Firth's distributional hypothesis (1957): 'You shall know a word by the company it keeps.' The core intuition is that words occurring in similar surrounding context windows tend to share similar semantic meanings and contextual functions. Dense word vectors (word embeddings) capture fine-grained semantic and syntactic relationships in continuous vector space.
""",
    # Page 4
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Prof. Richard Socher - Page 4 of 14

Unit 4: Word2Vec Framework Overview & Objective Function
Word2Vec is a computationally efficient framework introduced by Mikolov et al. (2013) at Google for learning continuous word embeddings from large unannotated text corpora.
The central principle of Word2Vec is to iterate through a text corpus using a sliding context window of size c. For each center word w_t at position t, the model predicts surrounding context words within window t-c to t+c. The parameters of the model (center word matrix U and context word matrix V) are optimized using gradient descent to maximize the log likelihood objective function J(theta) across all positions in the corpus.
""",
    # Page 5
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 5 of 14

Unit 5: Continuous Bag-of-Words (CBOW) Architecture
The Word2Vec framework defines two main model architectures: Continuous Bag-of-Words (CBOW) and Continuous Skip-gram.
In the Continuous Bag-of-Words (CBOW) model, the network predicts a target center word given a set of surrounding context words. The input layer averages or sums the continuous vector representations of all context words within context window c. The hidden layer passes this averaged context representation through a target projection matrix, applying a Softmax activation function to generate a conditional probability distribution over the vocabulary. CBOW operates faster than Skip-gram and achieves higher representation accuracy for frequent words.
""",
    # Page 6
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Francois Chaubard - Page 6 of 14

Unit 6: Continuous Skip-Gram Architecture
The Continuous Skip-gram architecture operates inversely to CBOW: given a single center word w_t, the model predicts the surrounding context words w_{t+j} within a context window of size c.
For each position t in a corpus, Skip-gram computes the conditional probability P(w_{t+j} | w_t) of context words using the Softmax function over vector dot products: P(o|c) = exp(u_o^T v_c) / sum_{w=1}^{|V|} exp(u_w^T v_c). Because Skip-gram treats each center-context pair as a separate training instance, it generates richer representations for rare words and small training datasets compared to CBOW.
""",
    # Page 7
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 7 of 14

Unit 7: Computational Bottlenecks & Softmax Optimization
Calculating the exact Softmax conditional probability denominator sum_{w=1}^{|V|} exp(u_w^T v_c) in standard Skip-gram presents a major computational bottleneck.
Because vocabulary size |V| routinely exceeds several hundred thousand or millions of words, computing the full Softmax sum for every gradient update step requires O(|V|) operations per word position, rendering full Softmax intractable for large corpora. Efficient optimization techniques such as Hierarchical Softmax and Negative Sampling are necessary to bypass this O(|V|) computational bottleneck.
""",
    # Page 8
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Christopher Manning - Page 8 of 14

Unit 8: Negative Sampling (NEG) Formulation & Objective
To solve the Softmax computational bottleneck, Mikolov et al. proposed Negative Sampling (NEG), derived from Noise Contrastive Estimation (NCE).
Negative Sampling simplifies the multi-class classification problem into a set of binary logistic regression tasks. For each positive center-context word pair (c, o), the objective maximizes the log probability that the pair came from true corpus data while minimizing the log probability that k noise words (negative samples) drawn from a unigram noise distribution P_n(w) co-occur with center word c. Typical negative sample counts are k = 5 to 20 for small datasets and k = 2 to 5 for large corpora.
""",
    # Page 9
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 9 of 14

Unit 9: Co-Occurrence Matrices & Global Count-Based Methods
In contrast to local context window prediction models like Word2Vec, traditional statistical NLP relied on global co-occurrence matrix factorization.
A term-context co-occurrence matrix X is a large matrix where entry X_{ij} records the number of times word i appears within context window c of word j across an entire text corpus. Global count-based methods (such as LSA / SVD) factorize matrix X to extract low-rank dense components. While count methods efficiently leverage global corpus statistics, raw counts scale poorly with vocabulary size and suffer from disproportionate frequency weights for common stop words.
""",
    # Page 10
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Prof. Richard Socher - Page 10 of 14

Unit 10: Pointwise Mutual Information (PMI) & PPMI Transformation
To normalize raw co-occurrence frequencies against chance word associations, statistical models calculate Pointwise Mutual Information (PMI).
The PMI between word w and context c is defined as log( P(w,c) / (P(w)P(c)) ). PMI measures how much more frequently word w and context c co-occur than expected if they were statistically independent. Positive PMI (PPMI) replaces negative PMI values with zero: PPMI(w,c) = max(0, PMI(w,c)). PPMI prevents noisy, unreliable negative logarithm estimates for rare co-occurrence pairs. Levy & Goldberg (2014) proved that Word2Vec Skip-gram with Negative Sampling implicitly factorizes a shifted PPMI matrix.
""",
    # Page 11
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 11 of 14

Unit 11: GloVe Architecture & Log-Bilinear Model
The Global Vectors for Word Representation (GloVe) model introduced by Pennington, Socher, and Manning (2014) combines the advantages of global co-occurrence matrix factorization and local context window prediction.
GloVe trains a log-bilinear model directly on non-zero entries of global co-occurrence matrix X. The objective function minimizes a weighted least-squares regression loss: J = sum_{i,j=1}^{|V|} f(X_{ij}) ( w_i^T w~_j + b_i + b~_j - log X_{ij} )^2. The weighting function f(X_{ij}) caps the impact of extremely frequent co-occurrences while scaling up rare non-zero entries, combining efficient global statistics with linear vector arithmetic.
""",
    # Page 12
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes by Francois Chaubard - Page 12 of 14

Unit 12: Linear Vector Arithmetic & Word Analogy Benchmarks
A remarkable emergent property of continuous word vector spaces trained on large corpora is linear vector arithmetic.
Dense word embeddings preserve semantic and syntactic relations as constant vector offsets in d-dimensional space. For example, the relationship 'king is to queen as man is to woman' is captured by the vector equation: v_king - v_man + v_woman = v_queen. Word analogy performance is evaluated using cosine similarity to retrieve the target vector closest to v_b - v_a + v_c under 3CosAdd metric.
""",
    # Page 13
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Page 13 of 14

Unit 13: Intrinsic vs Extrinsic Word Vector Evaluation
Evaluating word vector quality is conducted using two distinct benchmark paradigms: intrinsic evaluation and extrinsic evaluation.
Intrinsic evaluation tests word vector quality directly on isolated subtasks without integrating vectors into downstream neural architectures. Intrinsic benchmarks include word similarity correlation (e.g. Spearman correlation on WordSim-353) and word analogy accuracy. Extrinsic evaluation evaluates word vectors by using them as pre-trained input features in end-to-end downstream applications, such as Named Entity Recognition (NER), Sentiment Analysis, or Neural Machine Translation (NMT).
""",
    # Page 14
    """CS224N: Natural Language Processing with Deep Learning
Lecture Notes - Stanford University CS224N - Page 14 of 14

Unit 14: Subword Embeddings & FastText Architecture
Standard word-level embedding models assign a single vector to each word in vocabulary V, failing to handle out-of-vocabulary (OOV) words or morphological variations (e.g., prefixes and suffixes).
To solve the out-of-vocabulary problem, FastText (Bojanowski et al., 2017) extends Skip-gram by representing each word as a bag of character n-grams. For example, the 3-gram representation of 'where' includes <wh, whe, her, ere, re>. The final vector for a word is the sum of its character n-gram vectors. FastText enables computing meaningful vectors for unknown out-of-vocabulary words and morphologically rich languages.
"""
]

for text in sections_text:
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=11)

doc.save(pdf_path)
doc.close()
print(f"Successfully created 14-page academic NLP PDF '{pdf_path}'.")
