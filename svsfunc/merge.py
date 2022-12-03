import vapoursynth as vs
from vsexprtools import ExprVars
from vsrgtools import box_blur

core = vs.core


def detail_merge(clips: list[vs.VideoNode], weighted: bool = True) -> vs.VideoNode:
    """
    Merge N clips based on the frequency of each clip. Blurs each clip and compute the absolute distance between source
    and blurred clip.
    If `weighted` is True, clips are merged using a weighted average where the weights correspond to the distance
    (higher distance means bigger weight). Else, only the clip with the highest distance will be shown.
    `weighted=False` tends to produce sharper results and extract more detail but is more prone to re-introduce
    compression artifacts (ringing, blocking...)

    Goal is to merge starved source to try to extract the most details from each source while avoiding ringing.
    Merge isn't perfect and can introduce artifacts if both source are extremely starved but in different ways.

    :param clips:       List of clips to merge
    :param weighted:    If true, will use weighted average. If false, will return clip with highest distance

    :return:        Merged clip
    """
    clip_num = len(clips)

    if clip_num < 2:
        raise ValueError("You must provide at least 2 clips to merge.")
    if clip_num > 13 and b"src26" not in core.akarin.Version()["expr_features"]:  # type: ignore
        raise RuntimeError("You must have akarin plugin v0.96 or higher to use more than 13 input clips,")

    clips_blur = [box_blur(clip, radius=3, passes=2) for clip in clips]

    expr = ""
    expr_src = ExprVars(clip_num)
    expr_blur = ExprVars(clip_num, 2 * clip_num)

    # diff between src and blur (+ 1 to avoid having diff = 0)
    for i, (src_var, blur_var) in enumerate(zip(expr_src, expr_blur), 1):
        expr += f"{src_var} {blur_var} - abs 1 + D{i}! "

    if weighted:
        # sum of diffs
        for i in range(clip_num):
            expr += f"D{i + 1}@ "
        expr += "+ " * (clip_num - 1)
        expr += "S! "

        # get weight for each clip -> clip_diff / sum_of_diffs
        for i, src_var in enumerate(expr_src, 1):
            expr += f"{src_var} D{i}@ S@ / * "

        # merge weighted clips
        expr += "+ " * (clip_num - 1)
    else:
        if clip_num == 2:
            expr += "D1@ D2@ > x y ?"
        else:
            # there is probably a better way to do this
            # with x, y, z clips and a, b, c absolute diff between src clip and blurred clip
            # a > b -> DM = a & return x, C = x
            # b > a -> DM = b & return y, C = y
            expr += "D1@ D2@ > D1@ DM! x D2@ DM! y ?  C! "
            for i, expr_var in enumerate(ExprVars(2, clip_num), 3):
                # DM > c -> return C, C = C (could probably be optimised)
                # c > DM -> DM = c, return z, C = z
                expr += f"DM@ D{i}@ > C@ D{i}@ DM! {expr_var} ? C! "
            expr = expr[:-4]

    return core.akarin.Expr(clips + clips_blur, expr)
