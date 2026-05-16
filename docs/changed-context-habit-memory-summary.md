# Changed-Context Habit Memory Summary

This harness tests whether Habit-14 can protect a core pathway without becoming brittle when context changes.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Habit threshold: `14`
- Final exposures: `21`
- Final protection: `0.855`

## Result At Final Exposure Count

- Familiar-context adaptive/baseline improvement: `47.2079365x`
- Shifted-context adaptive/baseline improvement: `47.17974545x`
- Shifted-context adaptive/rigid improvement: `17.01315969x`

## Boundary

This is mechanism evidence only. The context vector is known to the adaptive memory, so the result should be read as a design test for context-aware protection, not as autonomous context discovery.
