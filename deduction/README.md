1. Load the LeanDojo corpus
2. Start the Lean server (use Kimina lean server, pegged to the commit used to build the corpus)
3. The dataset should be built as: theorems in Mathlib with known proofs. Then, the role of the model is to create a valid proof. 
4. Specifically, we have two knobs: a. how much progress towards the full proof we provide (e.g., how many tactics), and b. how much we elaborate that progress (e.g., we can either use a lemma as-is, or show the proof for that lemma, or show the proof for each component of the proof of the lemma)
5. We want to evaluate the difference between the intensional representation (just the theorem and the minimum partial proof) against the extensional representation (progressively larger elaborations of the partial proof)
6. Thus, we have two problems: a. how can we get ground truth proofs (and decompose them into steps) and b. how can we traverse the proof to elaborate each of those steps
. The prompt is: 
SYSTEM = ("You are an expert programmer and mathematician who helps "
          "formalizing mathematical problems in Lean 4.")
USER_PREFIX = ("Think about and solve the following problem step by "
               "step in Lean 4.\n\n")
SYSTEM USER_PREFIX Theorem

Start vLLM with a small model (e.g., DeepSeek Prover 7B, fp8) loaded for testing. 