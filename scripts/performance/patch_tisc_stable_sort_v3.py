#!/usr/bin/env python3
"""EXPERIMENTAL and REVERSIBLE performance patch.
Replace ONLY ReSort_Matrix's stable insertion procedure with a stable O(N log N)
bottom-up mergesort on the same previous-node order and same float elevations.
Do not promote to the scientific solver until strict 5km regression succeeds.
"""
from pathlib import Path
import argparse

REPLACEMENT = r"""float ReSort_Matrix (float **matrix, struct GRIDNODE *orden, int Nx, int Ny)
{
    /*
     * Experimental speed candidate (NOT official TISC): stable merge sort.
     * Prior insertion method maintains relative order of equal-height nodes,
     * so this intentionally selects the LEFT original item when zL >= zR.
     * Comparison uses the EXACT original float matrix, not rounded geometry.
     * All downstream code and physical model are unchanged.
     */
    size_t n = (size_t)Nx * (size_t)Ny;
    if (n < 2) return matrix[orden[0].row][orden[0].col];
    struct GRIDNODE *workspace = malloc(n * sizeof(*orden));
    if (!workspace) {
        PRINT_ERROR("FAILED TO ALLOCATE STABLE-MERGESORT BUFFER");
        exit(1);
    }
    struct GRIDNODE *src = orden;
    struct GRIDNODE *dst = workspace;
    for (size_t width = 1; width < n; width *= 2) {
        for (size_t left = 0; left < n; left += 2 * width) {
            size_t mid = left + width < n ? left + width : n;
            size_t right = left + 2 * width < n ? left + 2 * width : n;
            size_t i = left, j = mid, k = left;
            while (i < mid && j < right) {
                float lv = matrix[src[i].row][src[i].col];
                float rv = matrix[src[j].row][src[j].col];
                if (lv >= rv) dst[k++] = src[i++];
                else          dst[k++] = src[j++];
            }
            while (i < mid) dst[k++] = src[i++];
            while (j < right) dst[k++] = src[j++];
        }
        struct GRIDNODE *tmp = src;
        src = dst;
        dst = tmp;
    }
    if (src != orden) memcpy(orden, src, n * sizeof(*orden));
    free(workspace);
    for (size_t k=0; k+1<n; k++) {
        if (matrix[orden[k].row][orden[k].col] < matrix[orden[k+1].row][orden[k+1].col])
            PRINT_ERROR("UNSORTED!");
    }
    return matrix[orden[0].row][orden[0].col];
}
"""
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("file",type=Path)
    args=parser.parse_args()
    path=args.file
    assert path.name=="tisclib.c" and path.is_file()
    text=path.read_text()
    start=text.index("float ReSort_Matrix (float **matrix, struct GRIDNODE *orden, int Nx, int Ny)\n{")
    end=text.index("\n\n\nfloat calculate_sea_level",start)
    block=text[start:end]
    assert block.count("for (numorden=0; numorden < Nx*Ny-1; numorden++)")==2
    assert "Stable merge sort" not in text
    out=text[:start]+REPLACEMENT+text[end:]
    path.write_text(out)
    print("EXPERIMENTAL_STABLE_SORT_PATCH_OK",path,"previous_bytes",len(block),"new_bytes",len(REPLACEMENT))
if __name__=="__main__":
    main()
