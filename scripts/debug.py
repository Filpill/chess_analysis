import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    import re
    import marimo as mo
    return mo, re


@app.cell
def _():
    pgn = 	'[Event "Live Chess - Chess960"]\n[Site "Chess.com"]\n[Date "2024.12.16"]\n[Round "-"]\n[White "novebg"]\n[Black "hoshor"]\n[Result "0-1"]\n[Variant "Chess960"]\n[SetUp "1"]\n[FEN "nqbbrkrn/pppppppp/8/8/8/8/PPPPPPPP/NQBBRKRN w GEge - 0 1"]\n[CurrentPosition "n3rkr1/pp5p/4bp2/3p4/3N2n1/2P5/PPB3Pq/NQ2RRK1 w - -"]\n[Timezone "UTC"]\n[UTCDate "2024.12.16"]\n[UTCTime "20:00:56"]\n[WhiteElo "1808"]\n[BlackElo "1888"]\n[TimeControl "180"]\n[Termination "hoshor won by checkmate"]\n[StartTime "20:00:56"]\n[EndDate "2024.12.16"]\n[EndTime "20:03:31"]\n[Link "https://www.chess.com/game/live/128118042917"]\n\n1. Ng3 {[%clk 0:02:58.9]} 1... c6 {[%clk 0:02:57.8]} 2. O-O {[%clk 0:02:58]} 2... d5 {[%clk 0:02:56.2]} 3. d4 {[%clk 0:02:56.8]} 3... Ng6 {[%clk 0:02:48.1]} 4. c3 {[%clk 0:02:55.3]} 4... e5 {[%clk 0:02:45.5]} 5. dxe5 {[%clk 0:02:54]} 5... Nxe5 {[%clk 0:02:44.7]} 6. Bc2 {[%clk 0:02:49.2]} 6... g6 {[%clk 0:02:43.4]} 7. Bh6+ {[%clk 0:02:46]} 7... Ke7 {[%clk 0:02:38.5]} 8. e4 {[%clk 0:02:45.3]} 8... Be6 {[%clk 0:02:29.1]} 9. exd5 {[%clk 0:02:43.3]} 9... cxd5 {[%clk 0:02:28]} 10. f4 {[%clk 0:02:32.3]} 10... Ng4 {[%clk 0:02:22]} 11. Bg5+ {[%clk 0:02:22.9]} 11... f6 {[%clk 0:02:20.4]} 12. f5 {[%clk 0:02:09]} 12... gxf5 {[%clk 0:02:01.4]} 13. Nxf5+ {[%clk 0:02:04.8]} 13... Kf8 {[%clk 0:01:55.4]} 14. Bf4 {[%clk 0:01:59.3]} 14... Bc7 {[%clk 0:01:47.8]} 15. Bxc7 {[%clk 0:01:51.4]} 15... Qxc7 {[%clk 0:01:47]} 16. Nd4 {[%clk 0:01:46.6]} 16... Qxh2# {[%clk 0:01:45.7]} 0-1\n'
    return (pgn,)


@app.cell
def _(pgn, re):
    def extract_eco_url_from_pgn(pgn):
        match = re.search(r'\[ECOUrl\s+"([^"]+)"\]', pgn)
        if match:
            eco_url = match.group(1)
            print("ECO URL Extracted From PGN Data:", eco_url)
            return eco_url
        else:
            re
            print("ECO URL not found.")

    extract_eco_url_from_pgn(pgn)
    return (extract_eco_url_from_pgn,)


if __name__ == "__main__":
    app.run()
