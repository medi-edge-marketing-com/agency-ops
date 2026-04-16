#!/usr/bin/env python3
"""
SEO Monthly Report Generator
Pulls GA4 data and generates a clean, accurate HTML report.

IMPORTANT: This script only reports what the data literally says.
No interpretation, no recommendations, no narrative speculation.
The account manager adds context manually — this tool delivers the numbers.

Usage:
  python generate_report.py --property 514842555 --month 3 --year 2026 --client "Tierzero"

Credentials — set as environment variables or place in .env file:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_REFRESH_TOKEN

Output: report_<client>_<month>_<year>.html  (open in browser, Ctrl+P → Save as PDF)
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from calendar import monthrange

# Medi-Edge logo embedded as base64 (keeps report self-contained)
LOGO_DATA_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAtwAAADICAYAAADbcTbNAAAACXBIWXMAABcSAAAXEgFnn9JSAAABiWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSfvu78nIGlkPSdXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQnPz4KPHg6eG1wbWV0YSB4bWxuczp4PSdhZG9iZTpuczptZXRhLycgeDp4bXB0az0nSW1hZ2U6OkV4aWZUb29sIDEyLjE2Jz4KPHJkZjpSREYgeG1sbnM6cmRmPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjJz4KCiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0nJwogIHhtbG5zOnRpZmY9J2h0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvJz4KICA8dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPgogPC9yZGY6RGVzY3JpcHRpb24+CjwvcmRmOlJERj4KPC94OnhtcG1ldGE+Cjw/eHBhY2tldCBlbmQ9J3InPz40iwd4AAAgAElEQVR4nOy9f5Ac6Xnf9316BrhjzHj3quzIchRhkOhHnWlnZ3244y+XMBfLKlksGrMn8XCnH4VByZQoRarbqzgu5YcKg6pUlIpKvr3IEkOpbMyaIkGAJncg2iRtWYWBfp2EO2R3pZAni0lhV3bMWCoXMJFs3i1m3id/9Nszb3e//btnpmf3+VQtsDPT3e/bPb0z3376+zwPIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAiCIAhCJaFFT+C4cPQHH24S8SqgWiBeJcVN9xXVBHgFzAAY9W/9ROiYP3rzhRZhfBtwl/GWNX6/U3/XL7fmtzeCIAiCIAhCWdQXPYFl5NH9H2s54CbxuMWMBsBrYMAVyQQGA8STx2DzcQRUw0RgkyG4kbCeIAiCIAiCUGlEcKdgdP+/aRNUC+AWwGueMGaQVRyTIZpdqZwknOsAKS22jeXTCHVBEARBEASh0ojgtsD3f6KhHNUmcIuBC674dTAVwvALbVMYByLUfvEdIZzrdYDH8AnzUKRbEARBEARBWEZEcGv4frehTo3bYO4o5jXA0QI5zuZhvoaY1wzxHUktfgxBEARBEARhKTnRgpvvd1fHp5w2wB0FPg84YdEbF81OENh6lMBrNrSlxFsnGDGXCLcgCIIgCMLSciIFN3/1pxqK0VXgNhkVRDJHs2OsJNHi20YdRGM3om4bn6SYjCAIgiAIwrJyogT3o6/+dIuArgKfDwtlIDliHfUa4tdLWaWEjG2ExbcgCIIgCIKwjJwIwc1/9L91mMebANbc6iIphHHuaDYQK75t1OsA+6uUpEq2FARBEARBECrPsRbc/Ec/12HiLjOfAdUm4tc1aBjCe1bRbJtot1IHMI4ZXywlgiAIgiAIy4qz6AnMAv7jX2ypf/exPabaNaDmim3U3OYyVAPIAeCASP/AMV4LLhv4geOuT47ltaj1nOl6UcRtZ04NQR996bnuXAYSBEEQBEE4QRyrCDc/uNbgseox8XmwV3EESOPNJuM1NqPZmRIjIywoodeDeFVKYB/Dmb2lZPzl79lkwpVHX/7u1VN/6TObMx9QEARBEAThhHAsBDc/uLYK5Wwy4wqcYCt1m80D9teSxHdmK4n3GAnJj3WAAo1vfNuZbYSb33yhMSbu6n1/afTmh/bqT366N9NBBUEQBEEQTghLbynhB59sM07vsVO/YreARFg8TJuHZw+xLEvej2/ZgKUk1oJS869jo46E7cxWcCun1gfVVqbjO1tHf/Ch5kwHFQRBEARBOCEsbYSbH+yssvOox8wXIiPPKaLZkYmRloi1NfIdG822jGGlDkBFz3WGnSYf/ctOl0mtBfZjxVFOn+93mnS293BmgwuCIAiCIJwAllJw8/+302ZwD6itJHmzw68hw7IWO0lQfCNNmUEEthUkYCkJif/Ch8zK0R90mkR0xb3REbpoODN++6gPoDWb0QVBEARBEE4GS2Up4Qc7q+M/+dwWk7MDclYKVwyxLRuqEBKwhFgsKGT82LeTsUpJsCqKMxtLSY1O9ezHSs/VqZ1/9AffvzWTwQVBEARBEE4IS1Pgmf/0nzYZ6AFYm9osgnYNm30jYdnQa0jYZtJ46hCMA2Y1AAAF9/86Rgf09f/dwWyOTnbG//dHtgC8ZO4HR+6julz/lo/3FjdbQRAEQRCE5WUpBDd/7Z93oHgL4BVoA0ey+A3+jpjXkh4j6rUhgAFhPAB4D/XRHj3xcuU9z4/u/1jLYb5tPx6ARXwPFXPr9Lf09hY2aUEQBEEQhCWl8oKb/8OvupHYCGHMAaE4k2i2+Zj4FjEPMOYB/Sc/tHQClO9vripgD1Bn0l586Aucw1p9LEmUgiAIgiAIGals0iTz7VW87fQBnA8JQyMxkYzHXCgxMhDNnr42ZIW+46BPT/xAf177PysUqAvCGbcxEJDm2OhjfGY8JkmiFARBEARByEglI9z8tdcacFQf4LU83uyQFxnIYyW5Q4we8Fafnrh8LKK6oz/8u21i3omP/CPprsCrtW/6mHSiFARBEARBSEnlBDcf3W0CPAB4Jbc3O1Z8x4r2ITP3HPVoi5548WA+ezwf+H53VdXePkh/XCcCO/QaM1+uf9P/3lvEfgiCIAiCICwblRLcfHS3CXIG0MmRqT3WcRHaNOKb1SGBuxijT09sHItodhD1r36yz1AXckf+zYsU8NAhbtHZn186D7sgCIIgCMK8qYzg5rd/p83k9AhYcWflTS29lST6tfB6WnwfErhL7/xAby47uSBG/6bbJlXUShL6fd+heovObh3LCxRBEARBEISyqETSJB/d7TDzNbdlOib6b6q7jQS/uBbswZ+o14iHNMYmvfM7evPax0XB97urCrUeKHA8Irtier/D/tr0Z42hegDaC9kxQRAEQRCEJWHhnSZHX3uto9T4GjMDUNri4f4wdOUR7wcIdIgMdH9ERPdI32PnKt461TgJYhsAxo+d7gN5unKaxzTcXRNUA1Ptwvj+ZnexeygIgiAIglBtFmopefS1X285qN2eTGUyGwL5bCXT12j6i/F6kgUCAPgOeNShdzx7MLs9qhbjf/PTmyD1SnJVFsS8lmzXYcZG/ezPLH3JREEQBEEQhFmwMMF99Ke/2XRqPABjxZsGUVBge89Pf88hvodg7tBj7ztRgpC/+kpD0XgPwEpqb7bvMbKI76GjqEVnf1qSKAVBEARBEAIsxFJy9Ke3m4TxgJVa0VVCADCYFZgZPLGWuP+z8WPaTthqOyHTNnELpx5vnDSxDQBM6BHVViiLlcR8nM2us6Jq1OP7m6uL3GdBEARBEIQqMvekSX5we/WRoj5IrQDkVguBmylJ8DImjeeJQV4mJdHUyg24iXzsRrYZk82AgCGALp1+emvOu1cJ+N/+bJcJ570INBlRaQ4lP2LyWvaunNqOQjqJsvZ4D5JEKQiCIAiC4GOulhJ+cHv1UY0HANZM2wgFLCTuQwIM+4j3+9RGMrWYkO8x9omoQ6efOZH2Bv6jn2sy0a77IN46wmlKKabycRu/M67WzvzP3XntryAIgiAIQtWZq6XkyBlvMas11x5iWkO0lYQDdhH9vK9yiWct4anthDFZ9xadPt06qWIbALh2qme1hFDYEkLGj6Wai71KSVJ1E8e5MvrD/1Gi3IIgCIIgCJq5RbjfevArmwC/AvJi1GZUO1CVhLwlgpFv27pesiVfrb3j/d057Epl4X/3D7oMXMnduj1V5NuSXBl+beiQ06Jv6J7YCx9BEARBEASPuQjur/3xF1qo0e00AjqtyPY979Dl+jve35vHvlQVfnCtxUy3Q5aQzGX+putyts6T03W9TpSP0KKzXelEKQiCIAhzhplb+teG/gmyB+AhABDRYB5zOsnMPGnywYOdVYy57wZTGcEESfY9jl/GFeTT1xk0ZDit0+94/4mOpPKDa6uMU71QN8noBEfLa4H1mEFG50k32RLhZaM7Vq7xafQgSZTCAjG+cObNAREdlL1RZl4F0My42kMiOpafkfr9Pbb7l5ac50VZ7BFR6YGVnPs0k7+7ZUD/LXg/TQArGdcHgEO4InwPQL/Kf1fM3ID9ImLm5L04mXmE+z/88T8dAHzetYkEEhxjLSIx9hL3/yGIW6ff+WxlT4h5MR5+aouYX0pfYzvREhK73sRyAqRZ72rtP/3J7swPwhLAzB2k/4DYAzCYxRfZvNAfiE0kf2keEFGvxHE7ADYBrJW1zRxcJaJu0Y1o0dGBe+F6vuj2NPtwo1reF+telb9YTbSo6MAVFWf003eIqLWYGS0OfW5swj03FnmuP1tGdFR/XrRR7rl+R/8/AHAA9zP1oKRtLxzj76GNjAI7JUMAfQC9KkTA57C/qaBp05hs65U9EZN//29vdUF0xe7RTiO+jfX8gnwIh0RsA+AHn26xw7fDwhiIE83xryH1smnENwMb9b/435+4WuhBmHmA7F8ktwBsVeHDLg2GQOwgvQgoRTDpD+MepkJskRQS3IaY2sR8vliGcEXJAG5k62AOY6aGmZsAtmD/+zlxgltfVG5hgaLDoJDg1kK7C+BSSfNJwhORA7jn+tIFNfT738V8P+sOAXTLDI6kRX8e9gBcmPfYFg6JqJFnxZkJ7j/9o50mFO2SIZ4nPu3Ac/G+baP8n45sE6vW6Se+Q8T2g51VrvEBwCvJIjpfNBtRgjpWfAeEO/PQUeMWfcP/cKLfs5yC2+NVItoscTqlw8xtuB+KWUVAYcGkv4CuFdlGyWwQUa6LTH3h0MdixdQtuGKkt8A5AACYuQvgSswiJ0pwM3MP8xOnaTib9wKtIhcO26hIBDeJBQntIIcANvN+vmVFX2z3UY1AClDg82ZmZQF5xD0Y5f7YLOPne879nxXHLqOfE7FtwHWnB6qtxHeMNF8LlPmDE71eqARgoDygZYxJmUGExltRTr3H91+RTpT5eUl/0VYSPbcdLOCLUwv9KoltwI2eZUZ/od7G4iOXFwBcY+YDZl7YhZ4+r+LE9olCX3xUSWwfFhDbPbh/t4s+1y8BuK3P9c6C52KFmRs6YHMNixeeZwDsMPNA352YGUZke9H7bJL7QmMmgvtP/p9PdwFdb1uZItoT11HCmuPE93AEiNjW8L//fBtUuxCqtR0U0YmCOlhvO6v4Tlnj26mtqcdHJ7LzZ4lcqqLoXmTEzfhArhLbeW5TVzBKD7hfdK8sQoww8xaqJS4Xir7zUbWLj16elSr63p6Be5G5t8Bk6xD6gncP5fnay+I8gD0d8JgVW1hsfoKNXt4VSxfcf/qvbzaZ+Uoogs1BEa2fswhymOJb/6+YO+8UsQ0A4Ae3VwGnFx3NtjWtSRvNThDfkdF0y3hh8X1p/P/+TKVtEUvApYp9GSz6i3PRt6NtdLOuoCNFVb4g9cTIzKNawOSuxUuzHmfJ6C56AgGGyHHOLsF7uwY34r2lL+gXhg5mvILqfcZ5rMCNdpf+2aWtJFW7KLtaxPNfuuAe8XiLWQFKhSPYKthV0i7I2XgOSoEULv+ZP/ddJz7pbsJjoz7IWSE44U6RscI4PiodL76ziHbLeHo7RLVX+KuvtBZ38I4FlRBmWvgv+ouzamUnX855i72H6n6pmswjqgVU5ByvClp8VC3C2c4qPip6RyqKl+Ce63Mvt8jMq8y8h+oJzihmYXmsWnBuHwU/l0qtw/3gDz/RgVLnQeSvnc0EkFdPG5Pn3NrORs1ty3MMbP9HX/fBXpnzXHqo3gVGgFGZhkYjwEtEBQDiJoNfmSQw2mtlG78j5rWIx8GESmIQ49ng3EKPabR0WeEVY42ZWxVI8uktcnAt+KskUreJKE/Er4Xqiak4vKjWTBJ5tXWlSp7NKlC1C8vLOT9/5lV1pyzOANhl5svzSiDWFyUDVM9KkcQlZgYRdUraXquk7ZTBPoBW0Yo2pQnuB/evrUKpLYCmzWuYQEGh7Wtmo5/zCW2Y4vvOO//CRqesOR4X6B3PDpKW4T/5Asgh+Mr2xYpm22uIfi1iO/TnfjBxbkIpdJAzMa8MdIRz0aKoteDxPYZwy2XljX5ULZKTlpeYebXEL1iPZT0es2RRTW2CDOFGtgc511/W9/aaFpO9WQ6yxGLb4xIzPyzpQnzR3y8etwB0yigfWZ6lRDmbYLXiJT367SLaHqITJu1+7qB3Ww0ffa1yV/XLQ73u+qfh+afzeLMjkiNjq6IIc+LSgv2FnQWOXRWGAF4F0MwrtvV7WIXasnkpNZFX+8OXVWzMkkVXeDoEcBVAI6/Y1hfpyxTdDnJtDonDVUwSzMpLRS1ni7DxWLgFt8Z8ZutUFKVEuB/cv9ZgpTbBphUk0I6dCUyBNu7s1dn21nGXAxFIcfuJs98t1oPc1AEoXxSaJo1oyolmT19DYDvCnOhgAV5XLYqWVSTuo5woW1ntxFslbGPRlHkruQpftMeFbZRj+yqrXfpxeG9nFunW1Uhm6dn2Osx6NDC7KHKPmRsFhGreC8xnc64XZG8WDZFKEdzqEXfh8IprIYEW29oeYghteIaSgNBG4DkwXf2z/9nFQRlzO9GQdwPDL5rJEMx28R32Zsf7v43HwjzZxGKSyzoLGLMsHlbA+26SR4TcQXY7URPul9isvOKXmHlQghA5DqKsKhxU7Fxv5Vgnz7negnuuzypSfI2Z90q64AYwiei+Utb2MO2m2YcrHg8Sxm7pn7ICKStwv5+6JW0vFRU730MUFtwP3vxoY4zxJTfvzohsM4HI8HMjnfgm0P6f/cYXukXnJdQjhDFyim9bNNsmxIU5cmZByZOdOY93nMkTyRkUbBs/iy9YANgqW4gIJ56i53oL7nneRrkCvM/MzRKjoL2StpO5/br+e92D+/e7Clcol5Hc2iq4/rGjsIf7kYMujGY1rILl/rwSgWa5P/c5W9Ob8Vh1StgvAfWIcn3RjXKmfu84j7etxrd4uBdIZ56DVSRZ8jgx94guEe0R0RYRtQGchevNHZaw6RVUuOSbriFeORZ9XI4zRDQgoi4RNeGe69slbfoMSorests9tOjFwBBu5ZhGkbtMRPRQX+A04HqYi7BMlZfmQiHB/dU3P9ogxZc4kPjIbIrvsNAO1dqedKAcX33i7PdJdKQM6khZK9ueHBkS37E1vk0BL8yZSzzf5ElJZD5GENGB8QV7tYRNrvECW8ELQhT6XO/AFd5FxSTgJge2imyApxHlItyBm8zaK7idCVp4twFcRv6L8TIu4o8VhRRSjcddZktjGxXsMhkhvr1l3Gj3IaCk2UFp1BEXzY6tNBIQ4W6DHfcnWXwLC6Azj0H0l8Msk3qEBWFEttbh3pYuQnfOF4FpkWCO4AnvNoANFBeF3YLrF7VubBNR4frQUWgR30K+4yR/bwFyC+4Hu6+sMqtLpo3EL6ZN8c128a2mUW4aq84TZy9LVZIysZYAtJT6iy3z53/NL74tZQaFRTCviGJnTuMIC0L7OZtwKxrkxUuYqhqDRU9AqA5E1IcrJotcYJ7nnKUCS4hub8+gBn4I/ZnQyrFqr9yZLD+5BfdbdWxO/dpmlNuMWgf83DbxzQrM4ztPfPPlQYn7JQC6zrlOWo1t5R5uwR5vQQl6vo31hEVwpuitzZRUUUQJJaOjZS0UE92bVYtya4FVNHovHCOMC8wi50WnwHp5o9v78xDbHvo4vZxhlcN5deZcJvIrJMUdU1hPo9zhREhTaCMQ5YZSqI1GnfJ2SQAAjEbuewGzyVAa8W2I8KAlJU58e35vYVF0ZrlxLeglWfKEUILoXkE1/f7dRU9AqBb6XG8jv73kPOdr1NLJOd4QC/jb0s290iSdLmR+y0Auwf3V3f+1A1Zn/OI6aBkxxHhMlFtBbT/x5I8clLxfAoBJuT5PeIP1sU8hvlN1npROkxVi1smTnRluW6ggWoh0CmyicndEdNTtzqLnIVQLHcHtFNhEpnNdC/S8lUm2SmpElBkdVX8Z0Rcnd+B23hX/toVcgpuBti850ivxpwKRbaPNe5T4HiuJOMyCEWBUgTF/VFh8wxTfydFsnx88WB5QWCSdWWxUkiVPLvqLM2/1kjV2u5JWjTaK2WWEY4i2HOWtXpI1otvKOc5hkbrkZaBLiq7CTTq9qn8uAzirEzgPFjm/KpNZcH9196carMYXrJHtifiOqlQSEN9Q218v0e0ZMfIL7Djxzab4BsJWkjQWFF0eUCibLF8As4oodjIsW0a5LaFabCG/x7Vyt5YNu4ycq0KQvJ+hKxnzaPL+XXRzrlc6RNTXNc67RNQToZ1MZoU0VuO2T2yHPNwpxTczFI26M9gnQeMT0jbxDb8AjxbfwWh2jPgWymYP6cXOGXYb05RNli+h3gzGFxaIFqh5S7a2SpxKaRh1hjcg0W5Bo0Vj3uY4rQzL5mkK47VrF5aUzK3decSbcABi1m3aSbcHJ7ht2hnEBBB0m3fd1t1r+84AEYGYtv/CX375oNS9EaaMADgKALkt2yfvwxSe/EsgYoCnrzK5L02eIRhVSCwt4BmQ1u4zYwvAKymX7aDED+WMyZK3AEhpz+NJD+nPQZMyW8eXjrYR9LX1pQ2gUpVVhIXQQz4LXSvNQgUqSvVnVW9bmA+ZBPe/vtttKlZniF2JDSYQkc6/88S3KbQ98U1u1JRIC28GK+6VvTOCyQjMNUwEtXdRNBHfrN8tlyjxzZgsnlJ8CzOgj/Ri5wIzN0q8vdfJsGyvpDGFikFED5n5FnIIaGaufBKV/nuRxmsCiGjgNuLLXJUpbdQ6T0UTQOrILz2ZLCU8Ur5SgOFmN2ktJrz/9ev/7WBG+yR4sIIriHVSK7zygO7znrXEVzaQp7YS13ai/M+HKp0gYDMRykaLgSyVFTpljJsxWXKoo4XC8SXv+5tXYAjCohjkWSllecBGnm1D7CRLTzbBzaoV6c9W6cW3wkgiCXNgWrbRq4FuE9kB8W2K8szimxJmJBSgl2HZTkljZtmOfBkcf/JGqRtlTkIQ5sAg53ppLEl5LkAPxU6y/KQW3Pdf+4mGglpLlRwZL76Hj/C2fDnPmNFo5BPVqcU3R4jvUEJlhPgWZkUf6RszlJU82cmw7LJcRJ/n2TFY9M7NkgK2kEaZ8xBSc2WG53p30Ts3Y/Ke660Uy+TJEzjIsc6JY4bnO3MJ3ZzTe7jH1GZW2rPt+rLB7D72TL6YerShlzGTK7Wnu3/2XFeu1OaBFsJ+zzYH3i/P2z1ZKeDttqxPNLFrEyYvAxDBPSu0h7aP9BaPDgpEnTlbY4bDqnt0hdK4g+wVFhozmIcgzAwi2uPZBZDyNLwZFB10ARdJBzheiZ6Fv+NSC25WoxbBMQSYll8T8Q1DjANT8Q1DfAMKjkS35wSzW6UkOmHSE9+AKbR9CZTm9vT/ZGyH9YVXcFlhJvSQXnAXTZ7MUgpwWaLbs2aw6AkIwpw4CRfYQwArGdepcpWbKwsYc4uZu7ot/DIzLOPCIb2HW3GLeRxvG0ls7c7Db3z3T4rgngu68Y1KspPEW0zs6wbsJUaNb2F2ENEA2RqQdPKMw26yZBZLivxNu5yE43AShJaQzGDRE5gDec51SRD2swLgFealr0pXymd7KsH9ldubLWa1MhFjUZ5ta3dJU3yPTsIXUjUYIaWA9jcjCopvJIpvU7iL4J4DWf6GOjnHaCN9ZOeOdBgDcHJsNXmiPHmafAjVZfsY2QSE+XCJZ9OUbV70ythIOkuJQotJ6brbZp1tf0Mb1zZCummKtpFgujzjeJYNe/CVay12cNurMz41NgPh59xjCPitN0h4jrxjbjz3zq9rx7g4RmB2JuvFebm9xwCFnrP5vaN94CK458AWgJdSLnuGmds5yvVJZ8nsdBY9AUGYA0NUqL24kIk8+RdlsoXlvAt4S99dLkw6SwmPmyGbSKRtJBj55snjs+/7n5bxYCcywmgS9fVH+s3nLBFlxYEIc2CdSRUYDizjPpcIm+u59hJb9NofCU+wl8BY11bjW5gpOpqcpRV1J8v2MyZLAsv5AVo2r5b1gSwIFWdT7mgtLQcLHv8MMzcWPIesHKLEYEoqwW3W37aK7ZD4torGLI07lo+o/VdTIRu2boRtGqxsQtcQ2oaIjmNkWEqs1pFYb7dtPM9OFG8vEeZClgSUCxk/5LJEt+XWsnsMshyzZaeRY53j/dl/crhMRL1FT0LITXfRE8ByVSw6BNAu8zsuUXC/+YWPNFipFVcMji3i0Sa+xyExrlgNypp05dA1r80osTXy7/PAs1/YKv/6NvHNxnNIFLcjYzs233ba5MjAc0hYV5gHM7GISLJkJoYAXiaizqInMmcai56AMHcOAWycQLGdJwFyUPYkNIWrn+g7E1eLT+VEcAtAs+y8nETB7bBqmuIvVZMbQxx66yp1jAU3EBDOAXGrAsfDF/kPi29OFN/JEW53TuZ2g+LYtABFCWgVEuhTa0xU10ph1ugr7lsZVumkXC5LsuThCW3lfgj3S6txDEpd5aHKZc+EctkHcBmu8DiJf+tZSwKmJc8dn1KqnxBRF8CrZWzrGDIEsA3gWSIqNbLtkZg0qVg1ib0kSZ2jZ9TVdusw68Q+Jv/jSRIe8M3/1d8blD35SqGUv8EPCKwTSac1qo0mQUy6adC0Jfrk+Bk1sCd1zieJjOSKeUqqej0CKwdEgXrbetxw4qPZsCgqaTLwHBOIgjW+hTnRA3Ah5bIrzNxJEaHKYo1Y1i/gfWTbT5M9sdDkatpxUPYkhFRsI2dS80nPSdC5LHmY1edDo6wNEdGmbqLWQbYgyzLwbM71DuaRm5AouBnchGK/wDbFt1d5I158H3MPn1sRBGw7Tp74doWsV+llKr7dYwWf+DY7dAYEsVEdJmFKgKOMijJBEe02rAkK8uSqJklVTIR5QER9Zs7SmKGDmC/fHMmSkduqOA9PupjISwERclDmPITUHMi5npu853oaC8IA2auFnGHm1bIu+PV5MShjW1whL2nVz/fkpEk1Xk2qvW31dBvLEqtjXZ92mqAYTIRMY7mxJSqGEyyD1U+SLSWjiHmwZZyAT9wbV9msI/b1vP0S5kovw7LnE5InOxm2tX9Cak4Lflo515NzRVg2WjnXOyhpGRuVq2PNzK1Fz2GZSBTczOq83XfsT5S0VyuZCMyDOezLAjETFIMXIqboZfiFs3FcPXFr9YAHfdh6+fgZTcaMnIcpoi3PpRPfU2+3VCmZO72My8dZKTozHFc4HnRyrieCW1g28ojbYUpbQt6/h1bO9WZJ5S4Cqkys4N7d6azaRaQCc6BiSUypwNFofOw/cIMXGWExHYx0h6uOhCLh1jKDhviOYwRLgmb6Gt9h8Z2uhKAwP3SUuXCrd2buIJuPr5dhWeEYoO+O5PFvpxUhglAJdEfEPL7mVDpHf24PczIyyzMAACAASURBVGy/rStJVQkR3BmIFdx1vNWMjF5botlRgvHxt9463oLbKAvoqyiiLLWzA8fNJ86DlWCsZQanojlhUv4INQe3GV/jeyKsDUEeqrpiEd/C3MlSKWNFi+sgtueiuCWJgyeSTs71BiXOQRDmQd6k6iyJ5IMc219BhQSuvjA5k2WdqnusZ00aS0my2LY8ngq3Mc5u9I79F3SkXzvOYmKrrR2IiseJ7+Q5sbGNuNKDMfPwCfYU4luYN1mrhXTMBzpymSWBZ1mrkwg50VG1eYgQQVgo2pOct/35IMOyef8uujnXmwVZPxOylLI9lsRWKVEj1SIHCFYl8ZW801U3JuXrAo/pBHQZG2GEGjtuxQ6vrJ6txN+kOgjckoC6osu0CgkwKblolvLzSvIZ1U+SK4KMAOWE5gBjXl6lk2DpweA8EDk3Y7tG1ZWyeHv4q10AV4imx2F6vGCURpyWoUTk83y19o73d0udYAUgogNmvoX0JQLPM3PDuM2f5UNzeAKbX1SRed9W3kL+0mEiuIVlIm9t/cOMieR9ANdyjHOGmTcX3QNAR7ezXpic+M+ChAi3Gb0eR0dxA1FZX6RbnQBf7yjs4fb7pKcWE19EWUeI7YmmyRaTxDnZ5hAZ5Y5qsGPrUum914HId9KcsmJN1LR1xmS9HAeW48n6ZU+tYhTpPNmZ4TjCbCilCUYa9BfrpZyri/1IWBqYuYt8eQpAxs/GHM3LTLoJFadmir7jlUfwn/jvj1jBraKsIpbSgFah6b52vP3bAEy/dHSSaYpjlii+/RaT+BmNJsv7BL5VfLNFfJsXBXbxbRPCZaLgt7TYxXfUcwFBjmOtuPvIloTTAXIlS57EzopVpDGPQXTd7V6BTZz4L1ihMHO5uNQXllcKbCLPZ2Mv51grAPoLTKDcQkbvNoBtufhOENyOGrXsPu1xjPj2R8KVUifiIAfF8FR8J7V1j7pgCSRghiLOKQSkRWj7n7NVRwkLbfM5hMR3+ouAzNii6NYqKfHt5idlDY8p+oMsi7jxkic7GdbJestUmB1nCjShSYWOoPWR30pyKPYjoQRasxaWJVxY3spTiYeI+shWZcpkDQsIgOi7AHnuePXKnclyEu/hBvfAagB2dTk7DMABGHDAYDiAw663GA70C3DY0Z0KHcAZD2a+F4tmNAZqjtEa3d9tcuJxNvzdriV76o0nzwOt/d2u19p7JeC19paJndMIXKu5v9vayE/axEP7so3OkcZzk3U837np3db7Yz5XNq5wjms3b3jMjfbzZrdMmtHcKkYP2T4Iu8gWpehlWFaYPZvIXzkkFi1ABijW8rlbymSEk84K3HO9O4uN68BDkRwFoJjw7SKflxsALrHbLbpTYPzUMPMm8t0FuHPSq5N4xAru9Rc/15vTPJYeVsqaAOkmR0In8gWSJ8HTtu7MFpFLIGIEkysx2UaaOQUSMCdzYmNOYaEdL771vMykTq91fYkopUCTpEebgJ6K7+lxsbekP+5dMIlowMyHSC+is94S7GVcXpgtl5i5V/YXmf5S7aKYAJHotlAmm/pcPyhzo8y8BeClgpspJCaJqKejxlk/jz0u6Qvk9izr3TNzD/lzObrlzWS5SW7tLiTi90snetrLsZgkWiSM7pfGerFz8jXYsdTrVnElA2dgKYHFOuLzn8c34fHZS463h9ujN6Pt7kvzkkrSL8tawswtZh4AeAXFxDaQv4SgINgo1bPMzG12u18XFdtAOXeZiv69rAHY0xfLpcLMTWbeQ36xvS3R7SkiuMvA2tUxKtkxpfjm5PWTCArtUIWR2AY7yiK+w0I7lIBZJrY294bXPFl8T58TwV0ISZasJisABrp2cC60+BgAuI389YdN7mhvqiCUyRrccz3XBSYzrzJzRwvtHeSPKJtcLSMQof9eitaoXgHwCjMfRDQ3ywQzN3RUexf5K7cMIRffPmItJUJaRmDlaCeD55cGvPrlEz/3xN/NE3+3Z32Y+JJjLR/BGt8xMxoBjqOQp8b3ZE4Tm4jdCmOr8V0mf+brLnRxvG5HzTSBWNfk3kf+D8goREDNjj0UE7orAG4z8zaAraTEVi1YWnCrP+RtYR3FEBXqhCccO9YA7OpzvZskdvWFqHe+p+1TkJZ9IuqWuL0OgAMU/3s8A+Catsv09c8gTYUQnSjd0nMp4+K7I5VJ/IjgLgk36mo2tCHATWgIJPkFxK9PjBvJk3qZSA94orh1LwJsHnD/+GHx72+w4643Ed9eYyMz4dMnvoUY9lD+B3+QLeRPwrEh5ZxmS1nH9hJcP+cQ7nkWpIFyonpxyBesMA+8c/0QrkgN0kS5F5JBSr+wJKKHujTh7ZI2uQJ9nAAg8Lmwh+nnTkv/X/Yx25Y7XWFEcJfBaASuOf7EQk8cByqLxIvfbOI7EVbTSHtEAqZ1/Jgo97SjpBGNPxlVQMpgHmIkbwezuO1l4aDEsWdBQycpzZpBSu9i2aUWV1BOdCorL5f0BSulJ8ujNadzPW1C4wDlnptnMPuLSBszSVDUie8vw82jKBvzc2HWnw/786qcEmRO5zvy3t0QwV0CIwA1pdyg80S8Tsv6hSwZceLbakMJiG+jWkn0pEZgxwlUGTHnwwi3dDci8T7xDb/41lFuGHOiybaEGAazHkBHSraRP8nFZJhVRGlbyxCzjTAV4QyKNbjIwiDFMsdBYG6X2Gr6OByPqnAe87n4GiDdhfZxeG8vzzIJkIi2tO2rjM/vRbCPadS8CHmDU/P6bO/mWUmSJkvB6zTJ8QmT1u6SUQmUgU6QZgKkSpegaEvABPsTMP0t3SPGV+EqIL527rNKmjxmaH/t4RyGKutWXm/B4x97dKTszqLnUYDtMqNZ+njsl7W9Y8TBoidQFH3xnqUjbtW4PI9yl/rvaXvW48yAfQCtMmxlFW+ylvs7PDbC/dovvK8DchreY8fT587kH/d/x3tked1xBk//wBcHeSe4FIwArim7v9mLAnuRZi/yPUlgNJcPRJ6TbCixUxqhppwCNb6N8c3IOhOY2B55LzlpEgAe/KvrLQdOa/KEPrcc8wnH96LxtPtYOc7gP/7zHxyUPrl89DDjq3Ai6mesyR1Fr8B684jQDDC/iEZWBhmW7WExNpCizEqAlJ2HcBwoUppt1mQRR1uo7t9sFEO4NpLBvAYkIq+iyrIcq9LEtkEZ32GzIPfFQLylhFUHzOcnwoo8sQZMmo8QgxSmSXMEkJr6fnVL7UHeCS4HXoKi4bH2xLdhtbCLbze5MsmGQnodNoRuwpTAukoJYCQ2prGY6GRPGAJ9Mn7A1uLrrjmDpEli7gLq/OSigAmAcudBAKD0+eb+Pjk2isDk7r+jRkB1zsEtuKWSZm256KKYaNnPG2XQXsQ7mLGI1ONU0b4yzPLlrJtfdLA8onumAqSEZiDHkT5m4+0tyn5GkTWvz7+y2IebDDz3iCsRdbXoLtoJc9ZsA9icQcJ0H+XUSi+b3HdwYy0lSqkB8zhgiRgHakKPLXaDqUWBlCqlWH3VMY9BpE3E1mAmqW53TIOceEaJ62erEc6+9YMNfrwxSkf562xPGv949bWDtcktdbgTewTNEf2hNPPapDryWMSq0Cs4hQ7mc/u4ijXC83wgb2I5brffAtCYQ7SvM+PtLxUVth5l+vvTn3+d2UyldF4louYi7Q36c7yJatqshnDvcs2qOlEVP9uHmJXghvILr7BYGweE4TjQOGUMxaqUTmhVZjQahQRovIAdWwSt/aIlrkFOEtka7Jj+c46Ze4K/vGQYajXYYMfvO2f7PHzvw7hSfjD9IToPj14b+UVcIR+2FgjzaHqwhWoJ1VzNHvSXepWbRBwC2CCi9jxK/2lBf3XW4ywZVTs/9vNYirSXu8oe5TsA1omoEsebiA6IqAngZVTns+4WgOYsPe36O+TVWW0/J90in39JEe6A4BrHiO/oiO5JIDJB0hY99iUcxhy3yKh5itbuI/NOBEeMzRGdJc25c/h129w9IVw2Sq3ZLwDixPf0GDEzaMyVqw08j8QY/cHQQvYP6VsldVDrAbhcdDsJY1QtYpY72jOP45WDQ7hRrMa86+rq0ltVFmZzRV+UVeUiZIgCf3cVTQy8A+BZImpVMWlPVwJqwD0HFiW8vWM0k9KIFrqoTnT/VtFqTAlVStQg0haRUInDEOfL4ksswAgcEKNJNpE0kfCkZZNIPXaEeA7bUNhY37BuqKndo0we3L+2ap1DrPgOX0QQVU9wA5MvnZl+geovjqy3JEsTVlpEbmCGXxBaCFZBqF4uKkrncbxScgdTod1b1CT038jLixq/auiLkEVH/YZwE+QKidIKvbfbmArtwaInEwcRPdTnQAPud8c8ql4BbkR77sfICBotWnTfQgmBncSygNE2iHFAzAUfTwXc7rXW8fZxjxCKZtsFq3dMgr74ZB+1bdn4KY1SziWNBSb9+qUe1tGo6Y2HoDc7JL7DpQu95975Dc9XLlrhoT881zFDf2bGW5KFPGoR4/fhfkHMLKKlReE65vcFZHII98uoV8bG5nG8IrgF9xw5q79Ye3Me34qOKp1FNT3Mc0dbHRZ1UXYHrpWglM/UBb23Q7jn+mUAT2gP8mCO4xfGE95E1IB7Lmyj/M++O5h+Hsy1SouJIboXdaF5tSwrXWyVktEIe6fqbu0J159rdBcMdjwMNnwxHr/11ltNVKdKxAwYAcrx7bdXNm/ajREIVR+J6jA5aZUOTKuB6LXMaiMJU2JH+csKTuaiK8rYKo1YWr3HtnU3Kq9QyY1viLkBsK+TJcGrngL4KqyY1V985Q9LndJM0F9eLd3woAP3w2VtBuNsAdjSFTHaepxg9nt/Fh5dz/qhq0+09U+pd7/0cWwY+3ehzO1buAX3ePXK3rDleHVQ3jnhtXk+0P/vVV1w6NvXM/8bWRbILf3ZgHssOpjtsRjC/f7emsV5MuP39hDGeQ73XK9sACYP+gK9DwD6nGjBvWBvAVhF8rH0Pg8e6v8HcI9TZe4Me8UGmHkLrs2khdlWMdqHe0x7ZVpnEhXSb/z9Jk9Fi/7VS47T4sYr2RZ8TJ5wY3r5fT/6O1XMOC2FNz/XaTFw21fP2hOfUcfE9xiTixcyfp+UuPPKCk6edx//F62fiXz/7v/6T7SI6LZ5UWQf2zKXyXtpzMt4j729tO3j16/9ndJU9x//y491ieiKN6fQsfLmFJiD/zncWW38QKusOQnLhf4CapS82YM5+RdDaFGS547hw+MmNIDJ+7t6HPctKzM61xcmvJi5lXPVY3muC2EKnCNRzPTcSWztTo6zD8VrnuamSWSbdeRbTSOLgej2JMpLpX8IVIrRaASn5kyivOFa1dMIcCjaHBcJNyLfZDSwmbZWj8et1mFpehOoux2s8T2dtzlP+Mb2RbnTRt2zwqo1maMXxYYxP+Muiy3K7Z6j1blKF+aPFsYHC55GaYiQ8LOoC58qcgzP9cGi5yBUm2U7RxIFN4gOQFjz4pqTKDcw6W0DuLqOYRff2j9aGnf/4bODSQQWAODAcczopzcvBxOB6bnVyfFHkeE1L9TLBtb3RqnVsfmujU9HftmxUvA1uvEJbCNybFoxojpKWsT39EAbAjiO0Qhcc3c61PTGaLATaoBjabATKXQt4rtMmFXTZyHR+w6r7QUW8U1gKBEogiAIgiAslGTBDdojogs+oa3/nUZMp5KM9T+m+AZTqV5NZnV+MioRAAXF3sx0dJMB6E6DRAArL5qrAq3VCYrgJuZpMToVvcrdHyIcjSjmNu4IYCcsRI1Iv/l4ErmezNcQrZGRcBiR6mRxOwLgeBcBQaEfNw6M45jGWx7Y57L46puvNMC8EuxkGRT/8B3LsPh2IBFBQRAEQRAWS2KVEnKcPZAWPEQgcuB/rKOORG70OPgcu7aTX//ZZqu0WYeqaIwDlTym3S+DFTbC1T7s1VZCY8Shq5REV/kIzs+cQ6C2eWS5Pg5XB0mclKXaSNoa3xxRBSQ4l0Dt67KoqVoruka4fXzzOUyeOz63WAVBEARBWE6SPdzK2fMixWzEP/Wrkyg3YSq2vKUCz7VQUqUSVmMjqhqMshrR4Bgrhc+mgfCyUx+6GwnGKE5MjowIuq3CiB7TMl8vumzzwPsi34alZOK7jmMEcM0T5eFoNKLGCVphgpFwc59sVVZKgsfj1tS/zunGt0S5n/iWvy0RbkEQBEEQFkqi4H7vj/z2wW9/7N1DBlbIKw8HL4FPayBfBTa7+HZKzCZ1I5oUEo9BiwRCYjv6cchfbYhx96cWOZ8RAMcyp9CYNj+093vUxUGEDSWZEVg5qawgfvEdTK6M8qUH9sHnVS+OYtWyX7BMkz0n4hqESXKoeZxY3SltQoIgCIIgCDlJ4eEGQM6AwBcATKS0FxcNRblN8a0FkqY0HzcbfmsjMTO2AkisEDYeR0V3yYkJKY9GYCf/mGYC51RkxolvL1KfcJxY5a/xbbkjEB0Jn26rDL66+1MNZnXGfsESmI8h9M190Y8GpUxIEARBEAShAIkebgAgoj3Pu02GTzvs5fb83RYvNzn4rZ9/ql3GpMOeXu8n6L+2P7a3PPd7qVmNfZ7n0WiUMKkoT3RMV0nL43Qt1pN95aPRyPWOx3WIDO5r0IceN+eI/S3l/VVOO24+fr+211Uy7FdXLAmTgiAIgiAsnlQRbgVn4BBf8eKX0VFu0+xg83dzGyW0jZ5aSrxZ+COtdntIOCo7jaCGHwerjMTbJUbuslbvtZ5T8DWb/zkQGffPQc/dZ3VJOE6KMe0Qma3GtzVyHIrO22p8F0dBtYmnUXcY8/ONFeHvhj7Gp48eDUqZkCAIgiAIQgFSCe73fvg3Bnf/wV+DJ6KnQjut+J54uUuJcEMpe4OdJCuJKb69GUYIYTN5kgjAOGY+uo16WED7PcXBknV+YZ5dfMczArPRjCem/N/keFiTUNOKb0yWKcL93e4qxuo8e2ObF0+JFhPD381q/4n1l6XpjSAIgiAICyedhxsAE90i4MI0yu3JRZv4xuS3QJR75bc+9kz7fT98t1CUO9zdMhi9zhDNDnmBI6qDxLhvRhjB4RivtVXEW6qrTI6e/wIgUgTHMQK4No6N8MfX+A4nV/rFtxdr9gviotQeOW0mZR/bduciym9O5VTEEQRBEISqsHu93RgBjVlsuw4crL/YP5jFtqvC69fbLYecpiKsEnGTGKsAoKC7Vio1qD+OvfWNfukBu9SC26HaAFAXYMgsjywWEyrBVjIRpwwEGuxYxDaFXg9GoYPRbFvDGqJ4f7JbF9siACPFt130hh4HIvL+KHkcI0CRbz99FxKBY0Re98YUyZWRFwFlWEqYN2HrJBkam8PCnwkg14ainOoJbmbeAlBq11VBEBYPEbXSLnv3ZrtZY9oKvcDUdx5TvTK/6O/ebDcdRR2iwOcOce+p5/u9vNvdvd5ujBynQ8RNMB4S8cA5hX4Zc3/jRrsNUBfAWprlCbjDjD3lcO+Z5/uZ8nZ2r7cbY4e6ANoAVs5d3En1JRZcL/i6Il4PzuX1G891ibkDwpksc/Rg0NWnL362O3KcDoGv5NlGEiPQVQBd87ndnfbq6MjZ9ObuzSO47us3nuta5rUPcPfcxX4hzXfvZrvDTJsA1qLGjyP4fk00LJv6ld3CHg5dGR8Bb9zcuEXgfpG/kyCpBXcd6I+IXgF0JJM8kcPa3sCeHoK5DBAsIUjt3WvN1fXLe/n/MMmZmAkAJIhvmx8bKcX3VFSOxzH5paMR4PgjrD6RbK3+kRxxDkWgAyI4jhGAmlGqMLbGd+wFSZSVI89FQDz3X+s2wGrNLDMYmos5tuXiRO/X8C/+l3+3cK7ADGiixGo9giAsHzTGKjuWzwHi8+Mj6t692W5lFY5Bdnfaq+Mj2gLjkvcRb8LsDPJu+97NdmfMdI0MtcJMl8ZH2Co69zdubPQAXMqyDgPnQTjvML1078bGHUdxJ02UVu/HFiyCOY7Xr7dbY4f6UesR8eXgMXD3iy8ViUkR1B4AOKQOEu9wFxzDQ59HAwKv5Zz7GkA7b9zY2D53caeTdWVvfOZ0F18R62+NM55TAADGBQZdeOPGxqYi7hT9mwRSVikBgPXLgwNynEOz8ohXmcR9HFfFxJksC6KVtx49XsjLnba7pa3LY3zXR/vzbvWN+ColsduxVtvwVxCxdreMmIs3RiyjUUJHzYiKIzFVUWIfe8sXwOHRZnR3yfSVUpjVoNBEBEEQFsOKwzTY3WmvFtnI+Ii2kEdkJPDGjXabma5FvOzO/Xq7kWfbr994rouCc2bg/Nihvbs327F3Eu/ebDf1fmQS23dvtpsUI7YZdDUYEb13s91B0feCcehFiZ1T6AMYFtqenWHttP/O8PiIBkh5pyGBS298aiN8VycBdUT9vOPfvdlujt+mPRT/O1hzmHb1+1iI1IIbAAjUDwpr+MQ3pRDfBAfOZqFZRwnt0DyASXvyBPGd1OY9nqC4nQrqUOm9oKAMtKIPvxYUk8YcEygkoFVYiCcK4IJlAZlVJ095xPDr4ypGtwVBENKwMjrK/x1ZisCLwmaF8bOib91nYvd6u1GiTWLFYRrEiW6rpSeB3Z32qsM0QLRI37ZZHbh4sYihcniyDde2w52C2wyNwYrbpiVIn0dliG0XwkuvX2+30i7++vV2i3PeEb57s910mAZ57Ts2mOlaUdGdSXA7qtYLCmt7lDtOfDuAQ2uv/eJfa+WdNGlbw0Row5gHguLbiRDfloiuT7wFxHlMHe7RCKHlbeI7qsZ3ZDRbzyNfzetRhmi7/aIjcn6sL1YsAjgv93/tJzqs1EpC5Np479iYCxvzZTxyHlVScBNRiwRBOHaU/lnBBQQVU/51Y3j9eruVUsBkFpiKnHIqmE1ZiRLVuzvt1TxCTkd7o8T2fpRlwkvKy8EQwHZNcTNoZzh3sd9XxOsAtsE4zLl96HW3a4qbT7/YH/hfKqmqnAER9dLevSEn33k8EdsZ716kgZmuuTkG+Ujt4QaA9cu/svd/fPzbDxl0JpgiN63C7Lpop1VM/Mu4SxBqDjpAvsQ2IidY/SSwff0vs+Ephxbn7pquUIPf3zzxNHuG86lfmWKvTUZg5fdjZ6nx7X8cTGb0e8x93us4RgAcFenFNsfw9tTnyw6W+7OWXrTV+M4Hq9EmHCehxnew9F/AA+/O+9bZ9a6UAxQEYXkhnHnjRrudNdls93q7MZ5RnkgGAbRy72a7kyXZTBFWI7499lmxPdrvOK24JEQGzr9+vd0KCsnRW2hSplDjxFseFe3dr53mVrYtAnmS/0y0CO8En3/9ertFDt22rZM2KRQAoNAsow6CD8IZffemm7woGsHcgzQ4TD0kiW3CLQL31RgHk6ccrMK9yLAmwk5wL+RyBfUyCW53LGwR3ORJAIawnopZwC+97CUE+dJr11rd914eHGSetRae0+27I9JEmAXnEXjOFN+BZMuoaiLj2ColI4CdgBC2iOQMVVFSJXjGopvxeEI1kHyYVOM7qgSfT6hbkj7z8JXbf6fF4DViZSn1F3yM6T55x1XvH4jARL1ckxAEQagSRB1k/GIfExWza0bgJp+lj1zr6Giv6LgEPDwXEMwGg92d9lacX11fJEStn4p7n3puk8FRFp1hLWDFODaUaMfwb5av3L3Z7peRhBjEzQPgSBsMAUlJtf3dnfaqOqJ+5F2QAscl43Ue4NTqfYqxj1AGi0mNVTfPpL0xor3cwXmQxWJCvrkFky1Dfua4nMmRud44kEg4jrVixFsnYhIdVVwnHne6abzY8daWsO88yeqS6/3kcdc/Did7tu1e8+E3vrtbSTuJIAhCJhgXMicgUjjiWQbqUUTUL8rOkGfuOVjf6D+sneZNRCQRElBoDm/caLeZ+JWIl4eKuHXc61bPAh2FLpXdnfYqIeJuiMv2Uxd3Et+v9Y3+w6cu7rQAbFsXKGDhySy411/84gHIuRMnrO2iNyy+iZxLr11rNTLPOpQgmV98R643Ed86+TFBcduF8TggDGMqpnji3BTFEcI9lV9aVylBwENu3a5tzAQxHpW0mJWv/MpmC6zOx1WSSXvBoNS4l3kCgiAIFSVLxFondJXuWwUQ6Qsn0BaAfdtrM/BlW1nf6D8E26PpeZPuANcLDEQLQyLenEWU9oSwpqvSlEbkRSHcyHbWsoTnLu502K1L7r+Yo1hRH0tmwa3X6sUJ67DojSohSDiVwssThIwkScDYPuwiGpFCOxh9jxbfcYxGfnGeqsxgopg1hLA1wpxC3FrHiBDfgTGSEhcjo82ZGXXD43K64xSco6MyZ54LgiBUliwR6xklS+5ebzeihKvDqk8R0UqOjzaWChOVaunY3WmvOiqm1jbTy2U2RDmJaGtJaY3g4pI8HZUvCfnpi5/t1k5zA260e5sVP1ukiU8uwb3+4hd7oGlN7jhhnWjtcJxLuxmj3P5tOXYRbVQxiVwmdXQ8hV86gyi1i+9gJZMUVooUc0pnHUkTvY6OhGcpVWjylS98pMVGdDupPnjs8WXcOfve/+Ug0wQEQRCqRdAasZKmFFmkKC5SwUITE6neX3+xf+CwsgsQwpkyBVVOctWrVkfUj/Hqbj/1wmcluJOFiPOwVGsJ44L1ecKtIraf9Y3+w3MXdzrnLu50ggm4WckX4QZAcHphsWoR1hPh60wi0K6AnS6jHKeXbXBTRIf92KF5maUCY6PjMVHuJArU+E4sDxgSpONkcetF3XPW+E4U/JZIeNY63IpULxTFt1hxIsdV5rhiJxEEYekJi9cUkWur9YRwi2hahSEvUZFqIt4CgPUX+wcg3LIt46jZRN0tc7EKewIyWz7euLHRi4ro57EmCABHl7ksxVoSV9+bwJXJ68pcpcRDPV7fco5GV6ZSdFq+zVcthAjgacE5e0UROv/6x7+99fQP/ItBmrG9iHO4+ok3ByA4L3+FFFiXmcxLT81rMU7EYK7FzomZ3S1b2o1DbwcUXQXFX27PgYWt8QAAHsVJREFU/thcnhIqgowwgsPBSiLTih/evCYVSEJVSBBb2jBYZtC3ryn4/c//7U1mPgNW8JcVDFd1iWw1P53/4X/+bX+vl3pwQRCESsJ9gHwVMRg4v3u93YiN0lmsJ67QKCZ4795sN8H2SK/ueDgZi0HhCKM7r5laS16/3m5FRTcVaJBlW/dutjvMkU2D9p3TXJov3QG30orNulK9ZU7OfPrF/uCNT228CsJLwdcIvLl7vV1o/9ySfnaccbEqNWWSW3Cvb/Qf/u6nP7gNRZdCIpcxKd9Gup4yJrI3WDfbfa7mlhBqpBqcHHhy27+tqVyzie80y4QvHDQJR4r0nCY1vr2RgjW+jbKBZrm9qWA1hK8h1q1COAFW45DYzlbjO4XozTgnANjd6awycxfeuRFV43tyjKbHz1beUCfuCIIgLDXnLvb7b3xq4zBoZ9ARbKtw1SIx6DUeOqfQV0fFqpY4HJG0SbhllsJzTqE/PoKt5ftKnnriHgycv3uzHWr8Arg+a/W202HibtT6daV6mcaLbltfevk/Bs4TOG1SZ6+scRdF7THujt+mtsWqs6Ic6gFo5d02w2n69JpBnJC/d7PdyZX7QNzL4+HPLbgBYDyqdWs1dSkkYEkLbU2wJnZE05oz9z7+Hd2nfuCfd5PGnVhSYDbYSY5g25dJJ77rSZmTXsQ1TYOdYHTbE5bG46nYDUShvRkm1bwejQAHyFvje/LYHDNNBDoFj51Cj1mteHservGN6Ii/MRc97rBWq/VSDSwIglB9+kAgEhgXKbYLhv76Rv/hvRsbRedijegGb9Ovb/QfvnFz45Y10pyjnriJw7R778bGHfM5BlbHR1hzv3AjYLxaUlR4qIhb5xYVYWYcLnN022N9o//w9evtDlG4KQ8D5+996rnNeXvjFTuNDBc9U5jOv37juUbWxkW5PdyA591ytv2e7KlXO8rfHeW1dhy6svuJv5GYZGH3bbvbSUqSDC9jbitmvVjqdg87jPWtNb6DPu7w40hvc4oExbgqI0k1viMTNQMVTUKJjQl8+XPf32alLsTX+E6Z5MkKinnr7LNbx6/pgCAIJ5Ias010WJMno5IlWXGv6DziygyadhKPSK8s40Ladt5RMHDe/EF010eP/XMv7JRlZVlxOOXd9xkQ439eOnTS4bbtNSbuzqN2u4lD6iDvugk1v+3j5R3M41Qd3cxJjFbx7a2XIlqZscGOOYf4ZWLmHnMzoF63XQRM9xnBfQyI7+xJk1p8xzIKiNmUVUYKVFdBguDe3ems8ph7qauk2ES9f9nh6Xpd7CSCIBwbdDQzXNvaEsm2JksyDotWU3A3E1FmLWAn8dC32K1VQdTbTqfofDKwnafVejzUW0DFlSHAG2W8l1UiplGRZy2ZG84p9AtU8slc876w4H5yo39ADm37RW2WMnyhiiJru5/4zm7cmGlrfEdFsNMsE5x7ovkmtH+27Sc32JmK0EAE2BJ1jmM0Glmj2ROBHRGh9gldq/iOq64SfxFwit/qKVYrMQLacpER2G9jXaWURLcFQTh22Gpbe8mTgadtorhwVYbd6+1GZJk1jo2eW8dmmkOUlnDLrZO808nrtdaNTmysOIr6RSP1JgTcYdBV64/iZ2unuVGk5nNVcd8b+/nAwPk0ZTBDKDWIeikuar6+0X9Ye4ybALYJuBP1g4jmTlkp5OH2qBF3x+RcAqaO33QVRLxX/MsQ0ZXd6985WH/xiwPbeF5Cob/SCYxtG/5uZm0JcauPTGzSOjEvahkAbiUQ8uYVJ3DrIFKpEzD9lVqM5xjuOJ4PPMl/nQArXQHE2J75OFhlJOQxj0vwtCZiRs/ldz/zoY5idSE0ZjApEv75+n3mvvkdPv72SKLbgiAcO5zHVG98RKGW4mby5Bs32m0gXEEkwpKSCbf2ttUfPYwXgeEqK5q1xEor1s3hkMm9+NC38G1RxWHtNDfKSGh8+uJnu2/c3Gjaveg4Mz6iAYBSIt0KNMjqAT4unLvY70d5/plpa3en3VdH6bfHNTyMsvOrGlqISTrV500nbvuv33iuS+AkG1MipQjuJzf6B1/6zPdcBfGViWg2Xo8W32HROZV4tf7utXZj/bLlj4goJKwjxberVENzCCdW2uZpfORwYpkSv0BnBibi3h0oUmhbxTe7s7SI7cnjOEYjcM3xiVZ7mUEgWnwHBbV31I0KKkYyZVRe6e7NDzVZqS3Af8EQOeZklKkYtwj17tmNnkS3BUE4dkQmIZrJk0Qdy2fufhkJdpFdIhkP40rZed/uNuIqrURBhINzWpTeu9k+iKgisqItK6UEYGqnuKOFtU1grb1xY6MntbiLo4/zAcIXUSvjR9RLEVOc8Mzz/b03bmwMLdvyrFi9nNMEABBzJ02QM4nClhKPI2e0BXKGyb7pKOtGyN+94jx+ZL2SJt3l0mfd8MRcTIMd07ud1QMeK7frUTYXq2VmuhwMiwmC63pzA/ytzjN0dUyVmBnnFU+yuQS2yyp022V3p71KPOqx0laSrA12LD50Yt5/8gP/sJfqxBQEQVhG7NaNlXs3250oy4fXjKYId2+2m4jqskg4Q+ArcT8xmy5Uw/qp5/s9fXs/RJkJd+sb/Yc1xW1Ed6m8dO9Tz82tbf1xJc5aAsYFzn4nwW5nAs7HNcZJ4o0bbVspQyCi2VMcpQnu9Y3+QwfYTBLWmZIrndr5/Rsf7AXHYqY2yBn6hHVsa/Z4YZ1KfMdSt+xf3jbyTnrxHcvILlgTqqKkb0kfFN+8T2/XW6FpvKV6zGot2rcdU4klokrKaDSSDztBEI412roREn3MtDlynI5tHVv1kKxE1t4uCuGMtsHkZkyRlSFWxrXy+jGsv9g/YBXd5IaJXym6L4I+x6OFa8akxOiOkuTQVh7//e5OexVsP6/ydLAsTXADwJMbn+6B6E6SsE5Tvs+Ijl/63Zsf7JjjrH/f5/e4hhYRDYPCNFrQBsWrPfoetQzqKSwliVH8tOLbmIcpvn0XGPHTGY0wiQgnlt/LIYQDke6h80i1g/afe5/4ri1mdSEu8dEc2/dapOAfb/+VjV8a5Dk/BUEQlgzbl/qatSRZRPWQHMxQSEZUPknJM8/398B41foi40KZIvjpF/sDYno5eomFVC45dtROcQfRdxNSc+5iP67iyNr4iAZZRPfuTnt1fEQDa3SbcZin8U2pghsAuF7fDAvWLKX5bDWw6drvfdp/S2D9+c/vKS2609T4DtXIjpmDdZkY6gD8+5etxnd0RN52ETAV3/GMMkazx5mEsPH6UI1Va/3yFw/M0e/9o+/sgPmlxKojwZrecTW+lRo+wmMS3RYE4USgoi0iFq9q8drbWrBmLneWgUtFK33UHuMuogQa54tkRqEbsWxHvFx65ZKTSKy1JCvRd0AAYG38Nu2lsZe8fr3dGr9Ne4io905OdHfTOEpJmjR51wc+uffmre+9ClJX4hMS0ydX6sf9L91st95ltHhdf/7ze1+6+V2tEdcGAK8EEyen2w4maXrL0GRUcw62ZcARGYGAG/3WdbG9bWXpgDmdF4zlgvMw151uMw5XtHqJiu5Fgb3NO2Jates9MCqXGI+HALeeuTzwtd2994/+RoehrkGRO5S9yoil8yb0/6TnFngM6qxLoqQgCCeEZ57v79lavVtIqB6SEnsipq9aSOpNRfi51SO0USCJbX2j//DezfamNYGScGb8NnWRMTkzjtpp3hwfURM28VVy5ZJlxmE8TNlsOkRc1ZJSt0M4Q0S33/jUxiGAPogHrDDVFI7TInAbMY2VCLiTJ7oNzEBwA8CTFz7Z/f3PvdgGsBYlav0VQ2zLuBjie0URD4Ki+11adI9RGwC0YhfWsGw7XnwHBa5/dmGIHG+elguJ0L4gWwlBcx7JQttc2V5mMCy+zdeDbd79QtgT0DgkqrWDYvvutVZTKXXNi8KbJf+A6baSxbe2zUyrq9xae/4zx64mqSAIQhwE2mJwqESgD7YLWCY8TPuV4d5CjxQ8/awl7N64sWEVLux6xHtZthXkqef7vXs3Njps6bIJwkt3b7Z7zxg6wTd+TAk5G+sb/Ye7O+1WREUNIGflEmLu3Lux0cqwQi+v0MsDAXesxzcCxWovyQ0QR23Mm2OHWih4hyWhyoyLewH7EkAv+VP0Ek4MxqHzWLS3P4nSLSWTDTvUSZeQGOGbhtUDvgKHBl8K+Kbe9fzn92pUa4FoGGfT8D+Os3JYrB1JFm6f19rYF8N3bVuG9DKT44C4uQcsMwn49pERUXkkW+MZVgqs1P5pp9a0iW0wBrFNc2w+8oQkSVZqqE6NO1nPQUEQhKqhOwem9qw6rBIDDcqx20myJHbFdYOM2n4ctuY9mrVgRRGm5H0MEpNACSd6bM8HfphlrPWN/kNFsd0rs1cuIZzhQMv6uJ+0m+UaSrkLrECDLMtnPa+DrL/YPyCmbt71J9vZ6D/UnUZLaVYzgXGoHG4XyZOYmeD+lg98co+IriZXDPEL64mgdGzLOGCiFdScwZd2gqK7vzceO00C7UcJ68wJi8Yy8Xq7HrMv8fsbOy9DfNsEeiJR+xhRZtDelTIkhO987dSp1vrlge+ku/sL72vyWA2Y1UqwO2a6kn9Br7ghztU4d+cwQRCEqsFIX1Fj/cX+QWSioLuxw6hobpbW1ZHdIGO2H0fchUKwysozz/f3KKLkXxSxCZTAWpwAzuPBfeb5/h4RX456PbJyCVMpd2adMQZplstzQWGjflptIaOAznJe23jqhc9uZT0PbExEd47SfTYIuFN7jJt5/g5MZia4AeBbP/BLXSbnThpRGxTWQHRiI4hWwLWQ6F5/sX8wOuW0aDJmdOJkpuRKEGJD3L463CkSMHOWEJwu49UYj6FeT3ExESgzGCO+dYR6+70//NutZwNi+3c+9t62gjNgHq9krfFtPo5Imtxe/97PiZVEEIRjg7ZnbKddXicKWiN2FCNy1jf6D5UTW1MagK69HXELnjlfQtv6i/2DqFbpZNmmc5rbyBiVjDsucbW5tTUj9fFPv164conzmOpFzTE1jFczNTSKTx5MhRHVTy26s57XNvKcBzbWN/oPzz2/0wZ4I/cFCOOQiC8/dXGnVUbQb6aCGwAeO6q1iZxhpFXDFJmwCdbIyiYr4PrgSzsf8ovujf7Dv/KhfgtEryYJ62SRa1pDoqkDkfNMttRkKZEYEN8Jc5oul6PGd8j6Mb78vh95vRMc57WPvqejmHeYRwGxnaXGd2SDnX16+5RUJREE4dhx7uJORwvSREEzidi5EV3f8kmWk2ee7+/VFDfjIoeOoo7l6SHAG9oqkIunL362axXdhDPBahGGFSC1YFvf6D88d3GnGXEcY2tzn7u409Fl/zJFcRPWC1Uu8fYrb+SWQVfPvbCT6Xvw3MV+X0fjC5Xbe+b5/p6ibHPPcl7byHMexM+n3z/3wk4D4A29zaR5DUG4RcSXz72w0yjTN5/f4Z6Br3yh02Ko21M/OuuiH/oJ9lIBWT/F01+N57yW54C5DAOgy+/a+HQvOO6X/3G7zaCeAq/At64rLsPbMZZhIz2RGUz87PqLXxzY9m/349/eYtDtqH2bzD5m/23L2OZlLvOeH3ot8v177aPn9Jyijp+5j4G5mcsRHToOtd//X++FbqX81s+f2wTRK67FBfDuSnin1VTwG4/1shPhb3ns/kdDNUbrmcu/UugWjiAIQtXxxGcacbu7014dvTWtipFFEO9ebzdGQKMOHJgR03s32x3FTsN7TFB7pVQ9McZVNbTMMaDUIGru5j6m3b/gcfFIs/7r19stp4bM4spbz7dfQOS+3b3ZbjqMBsOJrWriMB4qVnv1x7FXNLJqXtgUuXjyzp0s23n9ervlkNPU5RWzj+m9p47TmjwZc96k3q6xLyZcw8OitpE45iK4AeArX+h0Ab4SFHhsCEL3iThhjQjxyGCmq+/auNkNjvvmTruhlNNj8HmrgA0I0Kg5KTjPrr/4Twa2fdv9+He2QOp26KJhssmYCwvLMvY5hOf+7g//Vozgfk8LpG5Pxb1/3HTiW20/Gjmbz768F/qD/42/v94D0SWyiW3LY6vAniSLustPHrtrb5y7/KtiJREEQRAEYemZSVlAG9/8N3vdP/jC5QYRX0JUuT6vZNzkFbNc33QdBNdzC9Bd+fLOh5pv45Evwe7Jjf4BgNb/+ZnnNonQBWgFevsMdkXhROQGtz0t1QdDm4aoA1BObJlBY56Jy5j7O53DdF6T2uBJeBFjY1lvSwk1vodj5s63/fjvhgTv7Veaq/UaD5jV2rR2txu95nApP1dDZ6zxrZiuvvsHByK2BUEQBEE4Fszcw21y6nHeBAWriBjVQJx0FUMiPdGOc+Fx57GQrxsA/vJ3f3bLcVSTCHd8yYeweaTDPuqkKxP/vOPnmWaZOH/35PU4jETOtCUR9ba3jx5x49t+fC8keH/9Z5utU3U+AGENjJxlBu3PG0ma2+/+wUE3y3klCIIgCIJQZeYquM8+23tYP80tMupl+0Qf0rRjjxffIFpzHGfw5V++GEoyeHKjf/Cu5z7bcog2iOjQXkUkQnzX4yR3PZWgpchlwvsWFt+e3SJdIidQh73Gt736CRPtO0TPvu9H73VsFpLf/Lm/2iWi2yBnJTSv1OI72NY9tPz+6VpNkiQFQRAEQThWzFVwA67orqHWAtHQXis7qlFNfJm9gGBdIdArX/7lF3zZwh5/aeMz/SMaN0F01augYotq+0oRJpAumpx00RAhvs3mOcYyKSZlOZ6m+CaAaEhO7fL7f+T15nt/5I1BcBOvffQ9jd/8+af2QHQl+mLCJr7DlUkSIt/7Xzt1OlTfWxAEQRAEYdmZu+AGgLPf8Yt7NTgtN9JtCNSApSRaxMZZNabrOEQXHq+/4+DLbpt5H+sb/Yfv2vjH3SMaNUC1q9BzsVk3ksRtvQ6faE6et034Tu0t7nj2CwtTRMfOCUGbS2heQ0bt6uOn39F47w/9ds+2jd/86DNdxniPiNYMgZ5wMeE9B6RtsAOlhmo87gTrewuCIAiCIBwH5pY0GeTsd/zi3v/1L36oQ+Ad8pIAmcDkJvMFk/r8iYWwLBNeBwCIsULgnd//3It3eMSdJzc+dWDOQydYdnd32lun6fQmwJsAr0zm5CUtci1mb+oAKd+cgomO0+cC8yQCeJo4GbVv9uTKuCnVAVawJGAegqn32Kn6VlQ0+bWPvqcFh7fAvAZdM8Q3dzOPlAlE3hMMJm9vvX/dNd1qMGwkVMIV6qAhoFq2soOCIAiCIAjHgYUJbgD4pm//hf79X/3wZQZdi6sQ4hex3mMXS4WNqGog56lO99/83PdefXx0euvsRs8nNk3h/RjqHRBtMnAG3ogJR2oacabJDKKqjGjd6W6ZWQtPc97mviWL7+Q5Aex2btp69w/+Ri9q+d1rrdW3Rm9vEeOSuS++uad9H0zxPRHXnvhW3p4NiUjEtiAIgiAIx5qFCm4AOPvXf7F3/1c/AoCvgXSUO0LkhUVsRFTbWCe4DIArb9ePNt/85e/dfPJvfbIXnI8W3lsAtt7ceaHFGHVA1E4qw0fkxM9bC+s0YjXthUUSRDQEqKeA3jOXB5Gidvdaa/VoNNo8Go82HdDKJHqtZxF54YCoi4LwXI07Dp74HpIjYlsQBEEQhONPmkDpXLh/+yMdKGxxoCtkZGOcVMsEG72EljlkxV2b8DbxEi+jOj793s73tEip2zDGjG6wM20skzzv+GX+6vf/SuT7t3uttZqUgLh7rbV6pNQmaRvNdLqBuRvzido/IFODnSERi9gWBEEQBOFEUBnBDQD3b/9oE6wGAFasojUgPvOJ2GBbdQDgQ0XcffzodD9oNUnD7+18T8thvu0ffwbzns4XALD+ff8s1/u3e621OgK0Xx0r0fP0z8c+z8ziWzzbgiAIgiCcKColuAEtusEDMFbCAhUZRGxAoFojriHxPSRSvbGjtp78m/7kyjje3HmhoaA6gGoBaIJ1tNicY4SwTiO+A8scEvGeUthb/74vdtPOEQB2r7WaY4c2AVyybx9WoW9bJnb/IpZh8P7RW+OWrc63IAiCIAjCcaVyghsA7t/+SINAfYDWosUnConv6Kist011xwF6p3JEvXd32qt11JsOqAHFDRCvgrlpjHM+QtQOAex5zxPzniI8JNDeWPHD9Rf/ySDLPAA3mo3aqbYibILV2uQFDl98+I+LnmuKZfTcfcsYS3nr77/12FHr2csitgVBEARBOFlUUnADwP3bm6vkjPpgPl/EmmEVgqktEQwAQzD3wdT/1g/+UqjdeRXZvdZaxenH2wC3wXwhPqo/kf6Zl7Efu/AxZ6jt9/7w3U55eygIgiAIgrA8VFZwexze+bEtZn5p8kSi5SEiCpsiqm1LyLQsc4uBgUM8+JYPfLIyPuTdT3xXE8Qth9BmxvlQdDrdvmHyqCzxDX75PR9+baucvRQEQRAEQVg+Ki+4AeAPf+3HO8y8BWAlLKynvyeL7+iodpqKIRbxOWRgAGDATHuPj+p7eZIus7K7016tj0ZNpZwWaNwEOy2wmlR3SSOsZy++MVSM9ns//BuDovsrCIIgCIKwzCyF4AaA+7+52ayNxz1mrEUL6+nvseI7wVJSqFwf8yGAAwYGUAAcNQAAjHAQ7HIZx5d22k01qq/WaLQ6ZqcJUqtgNAFuAliJ3DdjP7KWGYy5sAism7jMnVNOrZ1UllAQBEEQBOEksDSCG3B93fW66irGS+mj2rbnkoR1mmWmz09fDonv0Jye/Fufij3mv7fzPS0HuJ3FupEmkTSf+GZjk2mXoatPXx504/ZREARBEAThJLHwTpNZOPvs1kMAm3/4a5sDONyD4pVpq/Ng6/NpN0YGANJdDuE+YMR1rsRkvbhW85hsxVhHvxRsNT+dUzx11ME0NuY4xRsl2LkytK+p5p2mY2S4jTxHLUM4VArtuI6WgiAIgiAIJxFn0RPIwzd+21Z//IgacJxbRATvB5PfHf3Y0c85k+fhW46Mx8FloteZrqeXwXQ8//iWOaUhMO/wfhDgBOeUvK+2ffPP27JvoTkEjxuB4Lz6/7d3x7qNVFEYx78zO7uiY1sQS5JiC5CiOGWQYF0hbYVTbLECoTyCtaSgwyXFgvwAFE5NY5BAFEg7AYHb5AkSkQjaTYcA30Nhjz1jz4zHJkJK/P8VkWLdSc6k+nJ07r13gjcI2wAAAPNuVIc7a9ztbv32U7tlkXVdvjHb6c11mX3U4p7tahd3h8vWlHTCbfTFCtdMO8q1xJL5NJjPvUfaUfa0ZW+Tn26TZ2a7/PNrpu9bVnfxmnxX305N3t79+Mek7usBAACsmxsbuFNvvtftn71oJ3F8py0Ln82PmIzYNFeXBtI6oxn/fQxlkVhmw9LRmNnxjuL3WLxmubqna8Z/kysp6u5+tNxNlwAAAOvoxgduadLt7pwN2r04WE+yRzOdWJXPJI+Uz4AXdZDzzyw3J12DpdPe1TUtH75XqTu/xmRHwbyz+/SH87qvAwAAsM5uReBObe11zyU1L34+bCoadk3aKRiDUHGIXaaDvNwmxaJucRWzSLnu/LQguZVtEs3WnT53HXWP17gfh2DtxoffM6cNAACwhFsVuFMP3n2eSGpcDp4deFBH0kYukJrJvCp8L9NBrpqTnl+zSBzHch8W/4NgnjlppeLEkIpgXW++O1f3sQV1tp9+lywsHgAAAHNuZeBOvbH3ZU9S73Lw7ECujss2RhsONUmXpZsSVxjNsHEolldtUqwhM1JSdhRhUVf7usZQxr/5WIo620/6Sd2yAQAAMO9WB+5UGrwvBodNc3Vk4ZF7yebKzHO1z/jOPucmLzgNZdWRklw9rnEYL+9q13mPyvBtOvKh97affJvUKhYAAACV1iJwpx7sPU8kNf8YfLo51N8dyVrS6PKc6+ogS9OwW9QJr8VMhUfxmWdOWkl/dr6mOhfXFPwTcWVSN7Jh7639/nm9IgEAAFDHWgXu1Gt7n59LOjh70b5/95WoZR4dSL7gZJOizZUFazIjJUWd8IXiWOZh8m3uHOxx97zoVJG0muXCt39jbr2397/u1y0PAAAAy1nLwJ0aHyfYk9Qbdb3/aZn7gUw7ZRe+LBzfqHHBziJmUeEYSvrJoiP95mrKrzl1Rd0/h/f6u/u9l/X+UgAAAFjVWgfurHHXuyupm4ZvV2ia7IPVO8jpc8uPlBQG65mRkqoj/fLjIp6YqX/3r3v9LUI2AADA/4rAXSAbviXp918/aQVZU+5NN+1IFeHbxtfIrzhSEiuWW8g9M7shs/qiGsllxy4lkSl5+LiXLPv+AAAAuD4E7hpef+eLvqTJnPPF4LCpEJoyNSRtmkYhXKp3NnalWDKPZsZQys/KdtmpKZyYRyfBw8nDx0fJNbwyAAAArgmBewXj006S7GeXv7QbwbRpw6ihKNyX1PBgMvOG3F6dhu9FYsmG2bB95dKJSXILiYIpKCSx7OXW+19x6yMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALfJvxwyhV3nwPBhAAAAAElFTkSuQmCC"



# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_access_token():
    payload = urllib.parse.urlencode({
        "client_id":     os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "grant_type":    "refresh_token",
    }).encode()
    req  = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]


# ---------------------------------------------------------------------------
# GA4
# ---------------------------------------------------------------------------

def ga4_report(token, prop, body):
    url  = f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    })
    return json.loads(urllib.request.urlopen(req).read())


def rows(result):
    dh = [h["name"] for h in result.get("dimensionHeaders", [])]
    mh = [h["name"] for h in result.get("metricHeaders",   [])]
    out = []
    for r in result.get("rows", []):
        row = {}
        for i, h in enumerate(dh): row[h] = r["dimensionValues"][i]["value"]
        for i, h in enumerate(mh): row[h] = r["metricValues"][i]["value"]
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

def fetch(token, prop, year, month):
    _, last   = monthrange(year, month)
    t_start   = f"{year}-{month:02d}-01"
    t_end     = f"{year}-{month:02d}-{last:02d}"
    pm        = month - 1 if month > 1 else 12
    py        = year if month > 1 else year - 1
    _, plast  = monthrange(py, pm)
    p_start   = f"{py}-{pm:02d}-01"
    p_end     = f"{py}-{pm:02d}-{plast:02d}"

    dr = [
        {"startDate": t_start, "endDate": t_end,  "name": "current"},
        {"startDate": p_start, "endDate": p_end,  "name": "previous"},
    ]

    totals = rows(ga4_report(token, prop, {
        "dateRanges": dr,
        "metrics": [
            {"name": "sessions"}, {"name": "totalUsers"},
            {"name": "screenPageViews"}, {"name": "averageSessionDuration"},
            {"name": "engagementRate"}, {"name": "bounceRate"},
        ],
    }))

    channels = rows(ga4_report(token, prop, {
        "dateRanges": dr,
        "metrics": [{"name": "sessions"}, {"name": "totalUsers"}],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
    }))

    pages = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [
            {"name": "sessions"}, {"name": "screenPageViews"},
            {"name": "averageSessionDuration"},
        ],
        "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 20,
    }))

    daily = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "date"}],
        "orderBys": [{"dimension": {"dimensionName": "date"}}],
    }))

    devices = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "deviceCategory"}],
    }))

    cities = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "country"}, {"name": "city"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 40,
    }))

    nvr = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "newVsReturning"}],
    }))

    return {
        "totals": totals, "channels": channels, "pages": pages,
        "daily": daily, "devices": devices, "cities": cities, "nvr": nvr,
        "meta": {
            "year": year, "month": month, "last_day": last,
            "t_start": t_start, "t_end": t_end,
            "p_start": p_start, "p_end": p_end,
            "prev_month": pm, "prev_year": py,
        },
    }


# ---------------------------------------------------------------------------
# Number helpers — pure math, no narrative
# ---------------------------------------------------------------------------

def pct_change(new_val, old_val):
    n, o = float(new_val), float(old_val)
    if o == 0:
        return None
    return ((n - o) / o) * 100


def fmt_pct_change(pct, invert=False):
    """Return a plain +X.X% / -X.X% string with color class. invert=True means lower is better."""
    if pct is None:
        return '<span class="neutral">—</span>'
    better = pct > 0 if not invert else pct < 0
    cls    = "positive" if better else ("negative" if not better else "neutral")
    sign   = "+" if pct > 0 else ""
    return f'<span class="{cls}">{sign}{pct:.1f}%</span>'


def fmt_dur(seconds):
    s = float(seconds)
    m = int(s // 60)
    r = int(s % 60)
    return f"{m}m {r:02d}s" if m else f"{r}s"


def fmt_rate(v):
    return f"{float(v) * 100:.1f}%"


def get_period(data_rows, period):
    for r in data_rows:
        if r.get("dateRange") == period:
            return r
    return {}


def get_channel_sessions(channel_rows, period, channel):
    for r in channel_rows:
        if r.get("dateRange") == period and r.get("sessionDefaultChannelGroup") == channel:
            return int(r.get("sessions", 0))
    return 0


def us_cities(city_rows, n=6):
    seen = set()
    out  = []
    for r in city_rows:
        if r.get("country") != "United States":
            continue
        city = r.get("city", "")
        if not city or city in ("(not set)", "") or city in seen:
            continue
        seen.add(city)
        out.append(r)
        if len(out) >= n:
            break
    return out


def filter_pages(page_rows):
    """Remove pages that are clearly not content (privacy, legal, robots, etc.)."""
    noise = {"/privacy/", "/legal/", "/robots.txt", "/sitemap.xml", "/favicon.ico"}
    out = []
    for r in page_rows:
        path = r.get("pagePath", "")
        if path in noise:
            continue
        out.append(r)
    return out[:10]


PAGE_LABELS = {
    "/":                    "Homepage",
    "/switch/":             "Switch to Tierzero",
    "/contact/":            "Contact",
    "/about/":              "About Us",
    "/blog/":               "Blog",
    "/services/internet/":  "Internet Services",
    "/services/voice/":     "Voice Services",
    "/support/":            "Support",
    "/pricing/":            "Pricing",
}

def page_label(path):
    if path in PAGE_LABELS:
        return PAGE_LABELS[path]
    clean = path.strip("/").replace("-", " ").replace("/", " › ").title()
    return clean or path


# ---------------------------------------------------------------------------
# SVG trend chart — daily sessions
# ---------------------------------------------------------------------------

def svg_trend_chart(daily_rows):
    if not daily_rows:
        return "<p style='color:#9ca3af;font-size:12px'>No data</p>"

    values = [int(r.get("sessions", 0)) for r in daily_rows]
    labels = [r.get("date", "") for r in daily_rows]
    n      = len(values)
    max_v  = max(values) if values else 1

    W, H   = 820, 180
    pl, pr, pt, pb = 40, 16, 16, 28
    iw = W - pl - pr
    ih = H - pt - pb

    def cx(i):
        return pl + (i / max(n - 1, 1)) * iw

    def cy(v):
        return pt + ih - (v / max_v) * ih

    pts  = " ".join(f"{cx(i):.1f},{cy(v):.1f}" for i, v in enumerate(values))
    area = (
        f"M {cx(0):.1f},{cy(values[0]):.1f} "
        + " ".join(f"L {cx(i):.1f},{cy(v):.1f}" for i, v in enumerate(values))
        + f" L {cx(n-1):.1f},{pt+ih} L {cx(0):.1f},{pt+ih} Z"
    )

    # Y grid
    grid = ""
    for gv in [0, max_v // 2, max_v]:
        gy = cy(gv)
        grid += (f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" '
                 f'stroke="#f0f0f0" stroke-width="1"/>'
                 f'<text x="{pl-5}" y="{gy+4:.1f}" text-anchor="end" '
                 f'font-size="10" fill="#aaa">{gv}</text>')

    # X labels — show ~7 evenly spaced
    step   = max(1, n // 7)
    xlbls  = ""
    for i in range(0, n, step):
        day = int(labels[i][6:8])
        xlbls += (f'<text x="{cx(i):.1f}" y="{pt+ih+18}" text-anchor="middle" '
                  f'font-size="10" fill="#aaa">{day}</text>')

    # Peak marker
    peak_i = values.index(max_v)
    peak   = (f'<circle cx="{cx(peak_i):.1f}" cy="{cy(max_v):.1f}" r="4" fill="#D4AF37" stroke="#fff" stroke-width="1.5"/>'
              f'<text x="{cx(peak_i):.1f}" y="{cy(max_v)-8:.1f}" text-anchor="middle" '
              f'font-size="10" fill="#B8941F" font-weight="700">{max_v}</text>')

    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:auto;display:block;overflow:visible">
  <defs>
    <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#D4AF37" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#D4AF37" stop-opacity="0.01"/>
    </linearGradient>
  </defs>
  {grid}
  <path d="{area}" fill="url(#ag)"/>
  <polyline points="{pts}" fill="none" stroke="#D4AF37" stroke-width="2"
    stroke-linejoin="round" stroke-linecap="round"/>
  {peak}
  {xlbls}
  <line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt+ih}" stroke="#E0E0E0" stroke-width="1"/>
  <line x1="{pl}" y1="{pt+ih}" x2="{W-pr}" y2="{pt+ih}" stroke="#E0E0E0" stroke-width="1"/>
</svg>'''


# ---------------------------------------------------------------------------
# CSS bar chart for devices — more reliable than SVG donut
# ---------------------------------------------------------------------------

def device_bars(device_rows):
    d = {r["deviceCategory"]: int(r["sessions"]) for r in device_rows}
    total = sum(d.values()) or 1
    order = [("desktop", "Desktop", "#D4AF37"), ("mobile", "Mobile", "#B8941F"), ("tablet", "Tablet", "#E6C659")]
    html  = '<div style="display:flex;flex-direction:column;gap:10px;margin-top:4px">'
    for key, label, color in order:
        val = d.get(key, 0)
        pct = val / total * 100
        html += f'''
        <div>
          <div style="display:flex;justify-content:space-between;font-size:12px;color:#374151;margin-bottom:4px">
            <span>{label}</span>
            <span style="font-weight:600">{val:,} &nbsp;<span style="color:#6b7280;font-weight:400">({pct:.0f}%)</span></span>
          </div>
          <div style="background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden">
            <div style="width:{pct:.1f}%;height:8px;background:{color};border-radius:4px"></div>
          </div>
        </div>'''
    html += "</div>"
    return html


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

CSS = """
/* Medi-Edge Marketing brand: Gold #D4AF37 · Charcoal #1A1A1A · White */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #FAFAFA;
  color: #1A1A1A;
  font-size: 14px;
  line-height: 1.6;
}
.page { max-width: 920px; margin: 0 auto; padding: 0 0 64px; }

/* ── Header ── */
.report-header {
  background: #1A1A1A;
  color: #fff;
  padding: 28px 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}
.report-header .brand { display: flex; align-items: center; gap: 14px; }
.report-header .brand-name {
  font-family: 'Playfair Display', serif;
  font-size: 15px;
  color: #D4AF37;
  font-weight: 700;
  letter-spacing: .02em;
}
.report-header .brand-tag {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}
.report-header .divider {
  width: 1px; height: 36px; background: #333; margin: 0 4px;
}
.report-header .client-block h1 {
  font-size: 20px; font-weight: 700; color: #fff;
}
.report-header .client-block .sub {
  font-size: 12px; color: #999; margin-top: 2px;
}
.report-header .date-block {
  text-align: right; font-size: 12px; color: #999;
}
.report-header .date-block strong {
  display: block; font-size: 13px; color: #D4AF37; font-weight: 600; margin-bottom: 2px;
}

/* ── Body padding ── */
.body-wrap { padding: 0 36px; }

/* ── KPI grid ── */
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 28px;
}
.kpi {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-top: 3px solid #D4AF37;
  border-radius: 8px;
  padding: 16px 14px;
}
.kpi .k-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; color: #999; margin-bottom: 8px;
}
.kpi .k-val { font-size: 26px; font-weight: 700; line-height: 1; color: #1A1A1A; }
.kpi .k-sub { font-size: 11px; color: #999; margin-top: 6px; }

.positive { color: #228B22; font-weight: 600; }
.negative { color: #CC0000; font-weight: 600; }
.neutral  { color: #999; }

/* ── Section ── */
.section { margin-bottom: 30px; }
.section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .09em; color: #B8941F;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #E0E0E0;
}

/* ── Cards ── */
.card {
  background: #fff; border: 1px solid #E0E0E0;
  border-radius: 8px; padding: 20px 22px;
}
.card h4 {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; color: #999; margin-bottom: 14px;
}

/* ── Tables ── */
table { width: 100%; border-collapse: collapse; }
.table-wrap {
  background: #fff; border: 1px solid #E0E0E0;
  border-radius: 8px; overflow: hidden;
}
thead tr { background: #F5F5F5; }
th {
  text-align: left; padding: 9px 14px;
  font-size: 10px; font-weight: 700; color: #999;
  text-transform: uppercase; letter-spacing: .07em;
  border-bottom: 1px solid #E0E0E0;
}
td {
  padding: 10px 14px; font-size: 13px; color: #2D2D2D;
  border-bottom: 1px solid #F5F5F5;
}
tr:last-child td { border-bottom: none; }
tbody tr:hover { background: #FAFAFA; }
.tr { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.bar-cell { width: 90px; }
.bar-bg { background: #F0F0F0; border-radius: 3px; height: 5px; overflow: hidden; }
.bar-fg { height: 5px; border-radius: 3px; background: #D4AF37; }

/* ── Channel pills ── */
.pill {
  display: inline-block; padding: 2px 9px; border-radius: 99px;
  font-size: 11px; font-weight: 600;
}
.pill-direct   { background: #FBF8EC; color: #7A6010; }
.pill-organic  { background: #EBF5EB; color: #1A5C1A; }
.pill-email    { background: #FFF3E0; color: #8B4500; }
.pill-referral { background: #F3EBF8; color: #5B2080; }
.pill-social   { background: #FFF8E1; color: #7A5800; }
.pill-paid     { background: #FFEBEE; color: #8B0020; }
.pill-other    { background: #F5F5F5; color: #555; }

/* ── Two-column ── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* ── Footer ── */
.report-footer {
  margin-top: 48px; padding: 16px 36px;
  background: #1A1A1A;
  font-size: 11px; color: #666;
  display: flex; justify-content: space-between; align-items: center;
}
.report-footer .footer-brand {
  color: #D4AF37; font-weight: 600; font-size: 12px;
}

/* ── Print ── */
@media print {
  body { background: #fff; }
  .page { max-width: 100%; }
  .body-wrap { padding: 0 24px; }
  .report-header, .report-footer { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .kpi, .card, .table-wrap { break-inside: avoid; }
  .kpi { border-top: 3px solid #D4AF37 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""


def generate_html(data, client_name, property_id):
    meta       = data["meta"]
    year       = meta["year"]
    month      = meta["month"]
    prev_month = meta["prev_month"]
    mon_str    = MONTHS[month]
    prev_str   = MONTHS[prev_month]
    generated  = datetime.now().strftime("%B %d, %Y")

    # --- Totals ---
    curr = get_period(data["totals"], "current")
    prev = get_period(data["totals"], "previous")

    c_sess  = int(curr.get("sessions", 0))
    p_sess  = int(prev.get("sessions", 0))
    c_users = int(curr.get("totalUsers", 0))
    p_users = int(prev.get("totalUsers", 0))
    c_views = int(curr.get("screenPageViews", 0))
    p_views = int(prev.get("screenPageViews", 0))
    c_dur   = float(curr.get("averageSessionDuration", 0))
    p_dur   = float(prev.get("averageSessionDuration", 0))
    c_eng   = float(curr.get("engagementRate", 0))
    p_eng   = float(prev.get("engagementRate", 0))
    c_bnc   = float(curr.get("bounceRate", 0))
    p_bnc   = float(prev.get("bounceRate", 0))

    c_org = get_channel_sessions(data["channels"], "current",  "Organic Search")
    p_org = get_channel_sessions(data["channels"], "previous", "Organic Search")

    # --- KPI cards ---
    kpis = f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="k-label">Total Visitors</div>
    <div class="k-val">{c_users:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_users, p_users))} vs {prev_str} ({p_users:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Sessions</div>
    <div class="k-val">{c_sess:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_sess, p_sess))} vs {prev_str} ({p_sess:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Organic Search Sessions</div>
    <div class="k-val">{c_org:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_org, p_org))} vs {prev_str} ({p_org:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Avg. Session Duration</div>
    <div class="k-val">{fmt_dur(c_dur)}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_dur, p_dur))} vs {prev_str} ({fmt_dur(p_dur)})</div>
  </div>
</div>"""

    # --- Summary table (pure numbers, no narrative) ---
    def row(label, curr_val, prev_val, fmt_fn=lambda x: f"{int(x):,}", invert=False):
        pct = pct_change(float(curr_val), float(prev_val))
        return f"""<tr>
      <td>{label}</td>
      <td class="tr">{fmt_fn(curr_val)}</td>
      <td class="tr">{fmt_fn(prev_val)}</td>
      <td class="tr">{fmt_pct_change(pct, invert=invert)}</td>
    </tr>"""

    summary_rows = (
        row("Sessions",                c_sess,  p_sess)
        + row("Unique Visitors",       c_users, p_users)
        + row("Page Views",            c_views, p_views)
        + row("Avg. Session Duration", c_dur,   p_dur,   fmt_fn=fmt_dur)
        + row("Engagement Rate",       c_eng,   p_eng,   fmt_fn=fmt_rate)
        + row("Bounce Rate",           c_bnc,   p_bnc,   fmt_fn=fmt_rate, invert=True)
        + row("Organic Search Sessions", c_org, p_org)
    )

    summary_section = f"""
<div class="section">
  <div class="section-label">Traffic Summary — {mon_str} {year} vs {prev_str}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Metric</th>
        <th class="tr">{mon_str}</th>
        <th class="tr">{prev_str}</th>
        <th class="tr">Change</th>
      </tr></thead>
      <tbody>{summary_rows}</tbody>
    </table>
  </div>
</div>"""

    # --- Trend chart ---
    trend_section = f"""
<div class="section">
  <div class="section-label">Daily Sessions — {mon_str} {year}</div>
  <div class="card" style="padding:16px 20px">
    {svg_trend_chart(data["daily"])}
    <p style="font-size:11px;color:#9ca3af;margin-top:6px;text-align:center">Sessions per day · X axis = day of month</p>
  </div>
</div>"""

    # --- Channel breakdown ---
    ch_order = [
        ("Direct",         "pill-direct"),
        ("Organic Search", "pill-organic"),
        ("Email",          "pill-email"),
        ("Referral",       "pill-referral"),
        ("Organic Social", "pill-social"),
        ("Paid Search",    "pill-paid"),
    ]
    ch_map = {}
    for r in data["channels"]:
        ch  = r.get("sessionDefaultChannelGroup", "Other")
        prd = r.get("dateRange", "")
        if ch not in ch_map: ch_map[ch] = {"current": 0, "previous": 0}
        ch_map[ch][prd] = int(r.get("sessions", 0))

    ch_rows_html = ""
    for ch, pill_cls in ch_order:
        c_val = ch_map.get(ch, {}).get("current",  0)
        p_val = ch_map.get(ch, {}).get("previous", 0)
        if c_val == 0 and p_val == 0:
            continue
        pct   = pct_change(c_val, p_val)
        share = c_val / (c_sess or 1) * 100
        ch_rows_html += f"""<tr>
      <td><span class="pill {pill_cls}">{ch}</span></td>
      <td class="tr">{c_val:,}</td>
      <td class="tr">{p_val:,}</td>
      <td class="tr">{fmt_pct_change(pct)}</td>
      <td class="bar-cell"><div class="bar-bg"><div class="bar-fg" style="width:{share:.1f}%"></div></div></td>
    </tr>"""

    channel_section = f"""
<div class="section">
  <div class="section-label">Sessions by Channel</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Channel</th>
        <th class="tr">{mon_str}</th>
        <th class="tr">{prev_str}</th>
        <th class="tr">Change</th>
        <th class="bar-cell">Share</th>
      </tr></thead>
      <tbody>{ch_rows_html}</tbody>
    </table>
  </div>
</div>"""

    # --- Top pages ---
    pages   = filter_pages(data["pages"])
    max_s   = max((int(p.get("sessions", 0)) for p in pages), default=1)
    pg_rows = ""
    for p in pages:
        path  = p.get("pagePath", "")
        sess  = int(p.get("sessions", 0))
        views = int(p.get("screenPageViews", 0))
        dur   = float(p.get("averageSessionDuration", 0))
        share = sess / max_s * 100
        pg_rows += f"""<tr>
      <td style="font-weight:500">{page_label(path)}</td>
      <td style="color:#9ca3af;font-size:11px">{path}</td>
      <td class="tr">{sess:,}</td>
      <td class="tr">{views:,}</td>
      <td class="tr">{fmt_dur(dur)}</td>
      <td class="bar-cell"><div class="bar-bg"><div class="bar-fg" style="width:{share:.1f}%"></div></div></td>
    </tr>"""

    pages_section = f"""
<div class="section">
  <div class="section-label">Top Pages — {mon_str} {year}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Page</th><th>Path</th>
        <th class="tr">Sessions</th>
        <th class="tr">Views</th>
        <th class="tr">Avg. Time</th>
        <th class="bar-cell">Relative</th>
      </tr></thead>
      <tbody>{pg_rows}</tbody>
    </table>
  </div>
</div>"""

    # --- Audience ---
    nvr_map = {}
    for r in data["nvr"]:
        nvr_map[r.get("newVsReturning", "other")] = int(r.get("sessions", 0))
    new_s = nvr_map.get("new",       0)
    ret_s = nvr_map.get("returning", 0)
    nvr_t = new_s + ret_s or 1

    city_rows_html = ""
    for r in us_cities(data["cities"]):
        city_rows_html += f"""<tr>
      <td>{r.get("city", "—")}</td>
      <td class="tr">{int(r.get("sessions", 0)):,}</td>
    </tr>"""

    audience_section = f"""
<div class="section">
  <div class="section-label">Audience</div>
  <div class="two-col">
    <div class="card">
      <h4>Device Type</h4>
      {device_bars(data["devices"])}
    </div>
    <div class="card">
      <h4>Top US Cities</h4>
      <table>
        <thead><tr><th>City</th><th class="tr">Sessions</th></tr></thead>
        <tbody>{city_rows_html}</tbody>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin-top:12px">
        New visitors: <strong>{new_s / nvr_t * 100:.0f}%</strong> &nbsp;·&nbsp;
        Returning: <strong>{ret_s / nvr_t * 100:.0f}%</strong>
      </p>
    </div>
  </div>
</div>"""

    _, last_day = monthrange(year, month)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{client_name} — SEO Report {mon_str} {year}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="page">

  <div class="report-header">
    <div class="brand">
      <img src="{LOGO_DATA_URI}" alt="Medi-Edge Marketing" style="height:44px;width:auto;display:block">
      <div class="divider"></div>
      <div class="client-block">
        <h1>{client_name}</h1>
        <div class="sub">Monthly Traffic Report &nbsp;·&nbsp; {mon_str} {year}</div>
      </div>
    </div>
    <div class="date-block">
      <strong>{mon_str} {year}</strong>
      Prepared {generated}
    </div>
  </div>

  <div class="body-wrap">
    {kpis}
    {summary_section}
    {trend_section}
    {channel_section}
    {pages_section}
    {audience_section}
  </div>

  <div class="report-footer">
    <span class="footer-brand">Medi-Edge Marketing</span>
    <span>Google Analytics 4 · Property {property_id} &nbsp;·&nbsp; {mon_str} 1–{last_day}, {year} vs {prev_str}</span>
  </div>

</div>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", required=True)
    parser.add_argument("--month",    required=True, type=int)
    parser.add_argument("--year",     required=True, type=int)
    parser.add_argument("--client",   required=True)
    parser.add_argument("--out",      default=None)
    args = parser.parse_args()

    load_env()

    print(f"Fetching GA4 data for property {args.property} …")
    token = get_access_token()
    data  = fetch(token, args.property, args.year, args.month)
    print("Generating report …")

    html = generate_html(data, args.client, args.property)

    out  = args.out or f"report_{args.client.lower().replace(' ','_')}_{args.month:02d}_{args.year}.html"
    with open(out, "w") as f:
        f.write(html)

    print(f"Saved → {out}")
    print("Open in browser · Ctrl+P → Save as PDF to export.")


if __name__ == "__main__":
    main()
