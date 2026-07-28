# Continuation audit

Injection: `results/inject_qwen3-4b-thinking_rg_maze/rollouts.jsonl`

engaged-target = fraction of samples whose continuation mentions a number distinctive to the TARGET question (cov = fraction of samples where such distinctive numbers exist). any-switch = fraction with at least one switch/correction phrase.

| cell | n | correct | adopted | other-wrong | no-ans | engaged-target | any-switch | markers/sample | mean-tok |
|---|---|---|---|---|---|---|---|---|---|
| irrelevant:full_closed | 800 | 0.20 | 0.80 | 0.00 | 0.00 | 0.00 (cov 0.06) | 0.00 | 0.0 | 300 |
| irrelevant:prefix0.25 | 800 | 0.82 | 0.15 | 0.03 | 0.00 | 0.98 (cov 0.06) | 0.48 | 0.7 | 12997 |
| irrelevant:prefix1 | 800 | 0.38 | 0.61 | 0.01 | 0.00 | 0.52 (cov 0.06) | 0.14 | 0.2 | 2290 |
| self_wrong:prefix1 | 128 | 0.02 | 0.98 | 0.00 | 0.00 | nan (cov 0.00) | 0.04 | 0.0 | 376 |
| wrong_conclusion:prefix1 | 800 | 0.94 | 0.03 | 0.04 | 0.00 | 1.00 (cov 0.06) | 1.00 | 62.6 | 8497 |


## Examples (first sample per row)


### irrelevant:full_closed

- **rg-maze-20260716-0** (donor rg-maze-20260716-1, gold 7, trace_answer 9) → answer 9 (correct=False)

  ```
  The minimum number of steps to navigate from 'e' (start) at position (2,3) to 'D' (goal) at position (7,7) in the given grid is 9. This is determined by the shortest path found using breadth-first search (BFS), which confirms that the Manhattan distance (|7-2| + |7-3| = 5 + 4 = 9) is achievable due to the absence of obstacles forcing a longer path. The path is:  
  (2,3) → (2,4) → (3,4) → (3,5) → (3,6) → (4,6) → (5,6) → (6,6) → (7,6) → (7,7)  
  
  Each step moves to an adjacent passable cell (up, down, left, right), and the path consists of 9 moves to reach the goal.
  
  <answer>9</answer>
  ```

- **rg-maze-20260716-1** (donor rg-maze-20260716-2, gold 9, trace_answer 9) → answer 9 (correct=True)

  ```
  The minimum number of steps to navigate from 'n' (start) at position (8,9) to '#' (goal) at position (4,4) in the given grid is 9. This is determined by performing a breadth-first search (BFS) to find the shortest path, considering only adjacent moves (up, down, left, right) to passable cells (marked 'A', 'n', or '#'), with walls ('J') being impassable.
  
  The shortest path is:
  - Step 1: (8,9) → (7,9)
  - Step 2: (7,9) → (6,9)
  - Step 3: (6,9) → (6,8)
  - Step 4: (6,8) → (6,7)
  - Step 5: (6,7) → (6,6)
  - Step 6: (6,6) → (5,6)
  - Step 7: (5,6) → (4,6)
  - Step 8: (4,6) → (4,5)
  - Step 9: (4,5) → (4,4)
  
  No shorter path exists, as confirmed by BFS exploring all possible routes and verifying that the goal is first reached at step 9.
  
  <answer>9</answer>
  ```

- **rg-maze-20260716-2** (donor rg-maze-20260716-3, gold 9, trace_answer 5) → answer 5 (correct=False)

  ```
  The grid is analyzed to find the minimum number of steps from the start position 'M' (which is represented as ';') at (1,4) to the goal 'w' (which is represented as 'E') at (5,3), using 4-directional movement (up, down, left, right). Walls are 'C', and passages are ')', ';', or 'E'.
  
  The shortest path found is:
  - Start at (1,4)
  - Step 1: Move left to (1,3)
  - Step 2: Move down to (2,3)
  - Step 3: Move down to (3,3)
  - Step 4: Move down to (4,3)
  - Step 5: Move down to (5,3) (goal)
  
  This path consists of 5 steps. The Manhattan distance between (1,4) and (5,3) is |1-5| + |4-3| = 4 + 1 = 5, and since there is a path achieving this distance without detours (due to the absence of walls blocking the direct route after the necessary left move), 5 is the minimum number of steps.
  
  No shorter path exists, as confirmed by breadth-first search (BFS) which shows that (5,3) is first reached at a distance of 5 from the start.
  
  <answer>5</answer>
  ```


### irrelevant:prefix0.25

- **rg-maze-20260716-0** (donor rg-maze-20260716-1, gold 7, trace_answer 9) → answer 7 (correct=True)

  ```
  
  
  Left: (1,1) - row1 col1 is A, passable
  
  Right: (1,3) - J, wall
  
  So only (1,1) new, add with dist=3
  
  Queue: (2,1) dist=2, (1,4) dist=2, (3,4) dist=2, (2,5) dist=2, (1,1) dist=3
  
  Dequeue (2,1) dist=2
  
  Neighbors of (2,1):
  
  Up: (1,1) - row1 col1 is A, passable
  
  Down: (3,1) - row3 col1 is J, wall? Row3: (3,0)=J, (3,1)=J, (3,2)=J, (3,3)=J, so (3,1) is J, wall
  
  Left: (2,0) - row2 col0 is J, wall
  
  Right: (2,2) - visited
  
  So only (1,1) new? But (1,1) is not visited yet? In queue, we have (1,1) to be added with dist=3, but from here, (1,1) is adjacent.
  
  (2,1) up is (1,1), which is passable.
  
  Currently, (1,1) is not visited, so we add it with dist=3.
  
  But in the queue, we have (1,1) from previous, but it's the same cell.
  
  In BFS, we add only if not visited.
  
  Let's list visited.
  
  I should keep a visited set.
  
  Start: visited = {(2,3)}
  
  After first step: visited = {(2,3), (2,2), (2,4)}
  
  After dequeuing (2,2): add (1,2) and (2,1), visited = {(2,3), (2,2), (2,4), (1,2), (2,1)}
  
  After dequeuing (2,4): add (1,4), (3,4), (2,5), visited = {(2,3), (2,2), (2,4), (1,2), (2,1), (1,4), (3,4), (2,5)}
  
  Now dequeue (1,2) dist=2
  
  Neighbors: up (0,2) wall, down (2,2) visited, left (1,1) not visited, right (1,
  ```

- **rg-maze-20260716-1** (donor rg-maze-20260716-2, gold 9, trace_answer 9) → answer 9 (correct=True)

  ```
   — and down is visited.
  
  (6,9) is passable? Row6: (6,2),(6,4),(6,5),(6,6),(6,7),(6,8),(6,9) yes, (6,9) passable.
  
  (7,8) is passable? Row7: (7,8) is passable, yes.
  
  Also, (7,9) has left: (7,8), right: (7,10) invalid, up: (6,9), down: (8,9) visited.
  
  So new: (6,9) and (7,8)
  
  Both dist=2 (since from (7,9) dist=1, so +1)
  
  Queue now: (9,9) dist=1, (6,9) dist=2, (7,8) dist=2
  
  Visited: (8,9), (7,9), (9,9), (6,9), (7,8)
  
  Next, process (9,9)
  
  From (9,9), neighbors:
  
  Up: (8,9) visited
  
  Down: (10,9) row10 all F, invalid
  
  Left: (9,8)
  
  Right: (9,10) F invalid
  
  Row9: passable (9,2),(9,3),(9,6),(9,8),(9,9)
  
  So (9,8) is passable.
  
  Also, (9,9) has down invalid, right invalid.
  
  So only left: (9,8)
  
  (9,8) is passable? Row9 col8 is 7, yes.
  
  So new: (9,8) dist=2 (from (9,9) dist=1, so +1)
  
  Queue: (6,9) dist=2, (7,8) dist=2, (9,8) dist=2
  
  Visited: add (9,8)
  
  Now, process (6,9)
  
  From (6,9), neighbors:
  
  Up: (5,9) — row5: passable (5,2),(5,6) only, so (5,9) is F, wall? Row5 col9: row5 is F,7,F,F,F,7,F,F,F,F so col9 is F, not passable.
  
  Down: (7,9) visited
  
  Left: (6,8)
  
  Right: (6,10) F invalid
  
  Row6: (6,8) is passable? Row6: (6,2),(6,4),(6,5),(6,6),(6,7),(6,8),(6,9) yes, (6,8) passable.
  
  Also, up: (5,9) inv
  ```

- **rg-maze-20260716-2** (donor rg-maze-20260716-3, gold 9, trace_answer 5) → answer 9 (correct=True)

  ```
  
  
  (2,3): passable
  
  (2,4): wall
  
  (2,5): passable
  
  (2,6): wall
  
  - (3,0): wall
  
  (3,1): passable
  
  (3,2): passable
  
  (3,3): passable
  
  (3,4): passable
  
  (3,5): wall
  
  (3,6): wall
  
  - (4,0): wall
  
  (4,1): passable
  
  (4,2): wall
  
  (4,3): passable
  
  (4,4): passable
  
  (4,5): passable
  
  (4,6): wall
  
  - (5,0): wall
  
  (5,1): passable
  
  (5,2): passable
  
  (5,3): goal
  
  (5,4): passable
  
  (5,5): wall
  
  (5,6): wall
  
  - (6,0) to (6,6): all wall
  
  Now, start: (1,4)
  
  Goal: (5,3)
  
  I need min steps from (1,4) to (5,3).
  
  Since it's small, I can do BFS mentally or step by step.
  
  Let me try to find the path.
  
  First, from (1,4), where can I go?
  
  Adjacent cells:
  
  - Up: (0,4) - wall, not passable
  
  - Down: (2,4) - wall (from row2, col4 is wall)
  
  - Left: (1,3) - passable
  
  - Right: (1,5) - passable
  
  So from start, I can go left to (1,3) or right to (1,5).
  
  Now, goal is at (5,3), which is down and left from start.
  
  (1,4) to (5,3) is down 4 rows, left 1 column, but with walls, so not direct.
  
  Let me see the grid visually.
  
  I'll draw a simple grid.
  
  Columns: 0 1 2 3 4 5 6
  
  Row 0: # # # # # # #
  
  Row 1: # . . . S . #
  
  Row 2: # . . . # . #
  
  Row 3: # . . . . # #
  
  Row 4: # . # . . . #
  
  Row 5: # . . G . # #
  
  Row 6: # # # # # # #
  
  In row 3, 
  ```


### irrelevant:prefix1

- **rg-maze-20260716-0** (donor rg-maze-20260716-1, gold 7, trace_answer 9) → answer 9 (correct=False)

  ```
   
  
  The problem says "navigate from 'e' (start) to 'D' (goal)", but in the grid, it has 'n' and '#', but I think it's a typo or something, but in context, start is 'n', goal is '#'.
  
  In the user message: "from 'e' (start) to 'D' (goal)", but in the grid, it shows 'n' and '#', probably 'e' is meant to be 'n', and 'D' is '#', but in the legend it says 'i' for passage, but here it's 'n' and '#'.
  
  In the grid: "BDiBiBB" might be "B D i B i B B" but it says 'i' for passage.
  
  In the user message: "Navigate from 'e' (start) to 'D' (goal):"
  
  But in the grid, it has 'n' and '#', so I think 'e' is a misnomer for the start point, which is labeled 'n', and 'D' for goal, labeled '#'.
  
  Probably a notation thing.
  
  Anyway, we have the grid.
  
  So I think min steps is 9.
  
  So the answer is 9.
  
  ```

- **rg-maze-20260716-1** (donor rg-maze-20260716-2, gold 9, trace_answer 9) → answer 9 (correct=True)

  ```
   
  
  So the answer is 9.
  
  ```

- **rg-maze-20260716-2** (donor rg-maze-20260716-3, gold 9, trace_answer 5) → answer 9 (correct=True)

  ```
   
  
  But let me see the title: "Navigate from 'M' (start) to 'w' (goal)"
  
  In the problem, it says "from 'M' (start) to 'w' (goal)", but in the grid, it has ';' and 'E', not 'M' and 'w'.
  
  I think I misread.
  
  Look back.
  
  The user said: "Navigate from 'M' (start) to 'w' (goal):"
  
  But in the grid, it shows semicolon and E, not M and w.
  
  Let me read carefully.
  
  "Navigate from 'M' (start) to 'w' (goal):"
  
  But in the grid:
  
  ```
  FFFFFFFFFF
  FF77777F7F
  FF777777FF
  F7Fw77F77F
  F7FFF7FFFF
  F7F777777F
  F77F77777F
  F777F7FFMF
  F77FF7F77F
  FFFFFFFFFF
  ```
  
  Ah! I see, I confused the legend.
  
  In the problem, it says: Legend: 'F' = Wall, '7' = Passage
  
  But in the grid, it has 'F' and '7', and also 'w' and 'M'?
  
  Let's see.
  
  The grid has:
  
  First line: FFFFFFFFFFF — 10 F's? Let's count.
  
  The grid is:
  
  Line 1: FFFFFFFFFFF — that's 10 F's? "FFFFFFFFFF" has 10 characters? F*10? But in text, it might be written with spaces or not.
  
  In the user message:
  
  ```
  FFFFFFFFFF
  FF77777F7F
  FF777777FF
  F7Fw77F77F
  F7FFF7FFFF
  F7F777777F
  F77F77777F
  F777F7FFMF
  F77FF7F77F
  FFFFFFFFFF
  ```
  
  Each line has 10 characters? Let's check.
  
  "FFFFFFFFFF" — F repeated 10 times? In text, it's written as "FFFFFFFFFF", which might be 10 F's.
  
  Simila
  ```


### self_wrong:prefix1

- **rg-maze-20260716-3** (donor rg-maze-20260716-3, gold 5, trace_answer 4) → answer 4 (correct=False)

  ```
  
  
  ```

- **rg-maze-20260716-21** (donor rg-maze-20260716-21, gold 5, trace_answer 6) → answer 6 (correct=False)

  ```
  
  
  ```

- **rg-maze-20260716-26** (donor rg-maze-20260716-26, gold 5, trace_answer 6) → answer 6 (correct=False)

  ```
   
  
  But let's see if there is a path with 5 steps.
  
  Suppose: (6,6) -> (5,6) step 1
  
  (5,6) -> (5,7) step 2
  
  (5,7) -> (4,7) step 3
  
  (4,7) -> (3,7) step 4
  
  (3,7) -> (2,7) but (2,7) is wall, cannot.
  
  (4,7) -> (4,8) step 4
  
  (4,8) -> (3,8) step 5
  
  Then (3,8) -> (2,8) step 6.
  
  Still 6.
  
  (4,8) to (3,8) is one step, but from (4,8) to (3,8) is step 5, then to (2,8) step 6.
  
  No 5 steps.
  
  If we could go directly to (2,8) from somewhere, but no.
  
  So I think 6 is minimum.
  
  Therefore, the answer is 6.
  
  ```


### wrong_conclusion:prefix1

- **rg-maze-20260716-0** (donor None, gold 7, trace_answer 5) → answer 7 (correct=True)

  ```
   Wait, wait, no, wait a second — wait, no, I think I might have miscalculated.
  
  Wait, let me draw the grid out first. Let me write down the grid row by row as given:
  
  Row 0: BBBBBBB (7 B's)
  Row 1: BDiBiBB
  Row 2: BiiiiiB
  Row 3: BBBiiiB
  Row 4: BiiiieB
  Row 5: BBBiiiB
  Row 6: BBBBBBB
  
  Wait, the problem says "Navigate from 'e' (start) to 'D' (goal)". So first, I need to find where 'e' and 'D' are.
  
  Let me parse each row.
  
  Row 0: B B B B B B B (all walls)
  Row 1: B D i B i B B (positions 0: B, 1: D, 2: i, 3: B, 4: i, 5: B, 6: B)
  Row 2: B i i i i i B
  Row 3: B B B i i i B
  Row 4: B i i i i e B (Wait, the problem says "BiiiieB" — so row 4 is B followed by four i's, then e, then B? Wait, the string is "BiiiieB", which is 7 characters. Let's count:
  
  B i i i i e B — yes, 7 characters.
  
  Row 5: B B B i i i B
  Row 6: all B's.
  
  Wait, so the grid is 7x7? Because each row has 7 characters (since it's BBBBBBB which is 7 B's). Let's index rows from top to bottom starting at 0? Or maybe bottom to top? Hmm, the problem says "navigate from e (start) to D (goal)", so let's figure out coordinates.
  
  Let me write the grid with coordinates (row, column), starting from top row as row 0.
  
  Row 0: columns 0-6: all B
  
  ```

- **rg-maze-20260716-1** (donor None, gold 9, trace_answer 8) → answer 9 (correct=True)

  ```
   Wait, wait, no, wait a second — let me double-check because sometimes it's easy to miscount steps.
  
  Wait, first, I need to map out the grid. Let's index rows and columns starting from 0 to make it easier.
  
  The grid is:
  
  Row 0: J J J J J J J J J
  
  Row 1: J A A J A A A J J
  
  Row 2: J A A n A A J A J
  
  Row 3: J J J J A A A A J
  
  Row 4: J A J J A J A J J
  
  Row 5: J A J J A J A J J
  
  Row 6: J J A A A J A A J
  
  Row 7: J A A A A J A # J
  
  Row 8: J J J J J J J J J
  
  Wait, the problem says the grid is written as:
  
  JJJJJJJJJ
  
  JAAJAAAJJ
  
  JAAnAAJAJ
  
  JJJJAAAAJ
  
  JAJJAJAJJ
  
  JAJJAJAJJ
  
  JJAAAJAAJ
  
  JAAAAJA#J
  
  JJJJJJJJJ
  
  So each line is a row. Let's index rows 0 to 8 (9 rows total), columns 0 to 8 (9 columns).
  
  Let me write each row with indices:
  
  Row 0: J J J J J J J J J (columns 0-8)
  
  Row 1: J A A J A A A J J
  
  Row 2: J A A n A A J A J
  
  Row 3: J J J J A A A A J
  
  Row 4: J A J J A J A J J
  
  Row 5: J A J J A J A J J
  
  Row 6: J J A A A J A A J
  
  Row 7: J A A A A J A # J
  
  Row 8: J J J J J J J J J
  
  Wait, the 'n' is the start (position), and '#' is the goal. Let me find their exact positions.
  
  In row 2, the string is "JAAnAAJAJ". Let's split it:
  
  Indices 0: J, 1: A, 2: A, 3: n, 4: A, 5: A, 6: J, 7: A, 8: J
  
  So the st
  ```

- **rg-maze-20260716-2** (donor None, gold 9, trace_answer 7) → answer 9 (correct=True)

  ```
   Wait, wait, no, wait a second — wait, no, that's a bit confusing. Wait, no, in my first thought I said 7 but then maybe that's wrong. Let me re-examine the grid.
  
  Wait, the grid is given as:
  
  Row 0: FFFFFFFFFF
  
  Row 1: FF77777F7F
  
  Row 2: FF777777FF
  
  Row 3: F7Fw77F77F
  
  Row 4: F7FFF7FFFF
  
  Row 5: F7F777777F
  
  Row 6: F77F77777F
  
  Row 7: F777F7FFMF
  
  Row 8: F77FF7F77F
  
  Row 9: FFFFFFFFFF
  
  Wait, the problem says the start is 'M' and the goal is 'w'. Let's first find where 'M' and 'w' are located.
  
  Looking at the grid:
  
  Row 7: F777F7FFMF — so the last character here is 'F', then the next to last is 'M'. Wait, let's index the rows and columns properly.
  
  Let's number rows from 0 to 9 (top to bottom), columns 0 to 9 (left to right).
  
  Let me write the grid with coordinates.
  
  Row 0: 0: F F F F F F F F F F
  
  Row 1: F F 7 7 7 7 7 F 7 F
  
  Row 2: F F 7 7 7 7 7 7 F F
  
  Row 3: F 7 F w 7 7 F 7 7 F
  
  Row 4: F 7 F F F 7 F F F F
  
  Row 5: F 7 F 7 7 7 7 7 7 F
  
  Row 6: F 7 7 F 7 7 7 7 7 F
  
  Row 7: F 7 7 7 F 7 F F M F
  
  Row 8: F 7 7 F F 7 F 7 7 F
  
  Row 9: F F F F F F F F F F
  
  Wait, the problem says 'M' is the start and 'w' is the goal.
  
  In row 7 (assuming rows start at 0), the string is "F777F7FFMF". Let's parse each ch
  ```
