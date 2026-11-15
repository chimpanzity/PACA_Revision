# make_table2.R - regenerate Table 2 (Brown-Rosenthal profiles by model and prompt frame) in base R.
#
# PROVENANCE. The published Table 2 was produced on 10 July 2026 by the v92 statistical audit
# (Python, specification "paca_lag_only"; archived under docs/provenance/brown_rosenthal_v92_audit/).
# make_table2.py in this folder is that computation; this file is the same model, tests and summaries
# in base R, using unpenalised glm() as the audit used unpenalised maximum likelihood.
#
# MODEL (per session, trials 3-200, n = 198; all variables 0/1: choice 1 = TRIANGLE, outcome 1 = win):
#
#   logit P(choice_t = 1) = b0 + a1*own_{t-1} + a2*own_{t-2}
#                              + b1*proteus_{t-1} + b2*proteus_{t-2}
#                              + c1*outcome_{t-1} + c2*outcome_{t-2}
#
# Own, Opp and Outcome are each tested by deleting that pair of predictors from the full model
# (likelihood-ratio chi-square, 2 df, p < .05), counted over the seven sessions of a cell. The lag-1
# coefficient is a1 from the full model, median over the seven sessions.
#
# NOTE ON THE CONTEMPORANEOUS OPPONENT TERM (suggested by Rahul Bhui, September 2026). Brown and
# Rosenthal (1990) and the matching-pennies adaptation in Martin et al. (2014) include the opponent's
# current-trial choice, proteus_t, alongside the lagged terms, and there is a good case for doing so
# here: it is the standard form of the regression, it makes the PACA table directly comparable with the
# human and chimpanzee results, and under the equilibrium null the current choices of two simultaneous
# players should be independent, so the term tests the same hypothesis from another side. Table 2
# reports the six-predictor form because of how PACA is played: Proteus commits its choice before the
# model is called, so proteus_t summarises the lagged history the model already responds to rather than
# acting as a separate influence, and the paper's question is about history-dependence. Run
#
#   Rscript make_table2.R plus-current-opponent
#
# to add proteus_t as a seventh predictor (1-df deletion test). The two specifications agree closely on
# the main data: the term is significant in 9 of 98 sessions, 9 of the 14 cells keep identical
# Own/Opp/Outcome counts, and no count moves by more than two sessions. Either form could serve as the
# primary table; the paper presents the six-predictor version and reports this one alongside it.
#
# SEPARATION. Three Sonnet informed sessions alternate almost perfectly, so glm() will warn that
# fitted probabilities are numerically 0 or 1 and the own-choice coefficients for those sessions are
# huge. That affects neither the likelihood-ratio tests (the log-likelihood converges to its supremum)
# nor the cell medians, which fall on non-separated sessions. The warnings are suppressed; the affected
# sessions are counted in the "fit_issues" column.
#
# Usage, from this folder or the release root:
#   Rscript make_table2.R                          # published specification, checks against Table 2
#   Rscript make_table2.R plus-current-opponent    # Brown-Rosenthal / Martin et al. (2014) form

args <- commandArgs(trailingOnly = TRUE)
spec <- if (length(args) >= 1L) args[1] else "published"
if (!spec %in% c("published", "plus-current-opponent")) stop("spec must be 'published' or 'plus-current-opponent'")
current <- spec == "plus-current-opponent"

candidates <- c("data/trials_compact.csv", "../../data/trials_compact.csv", "../data/trials_compact.csv")
csv_path <- candidates[file.exists(candidates)][1]
if (is.na(csv_path)) stop("trials_compact.csv not found; run from the release root or from code/table2")
d <- read.csv(csv_path, stringsAsFactors = FALSE)
d <- d[d$dataset == "main", ]
stopifnot(nrow(d) == 19600L, length(unique(d$session_id)) == 98L)

fit_session <- function(g) {
  g <- g[order(g$trial), ]
  n <- nrow(g)
  own <- as.integer(g$subject_choice == "T")
  opp <- as.integer(g$computer_choice == "T")
  win <- as.integer(g$subject_win)
  idx <- 3:n
  dat <- data.frame(y = own[idx], own1 = own[idx - 1L], own2 = own[idx - 2L],
                    opp0 = opp[idx], opp1 = opp[idx - 1L], opp2 = opp[idx - 2L],
                    win1 = win[idx - 1L], win2 = win[idx - 2L])
  ctrl <- glm.control(epsilon = 1e-10, maxit = 200)
  qglm <- function(f) suppressWarnings(glm(f, family = binomial(), data = dat, control = ctrl))
  lr_p <- function(reduced, full, df) {
    stat <- 2 * (as.numeric(logLik(full)) - as.numeric(logLik(reduced)))
    stat <- max(stat, 0)
    pchisq(stat, df = df, lower.tail = FALSE)
  }
  if (current) {
    full   <- qglm(y ~ own1 + own2 + opp0 + opp1 + opp2 + win1 + win2)
    no_own <- qglm(y ~ opp0 + opp1 + opp2 + win1 + win2)
    no_opp <- qglm(y ~ own1 + own2 + opp0 + win1 + win2)
    no_win <- qglm(y ~ own1 + own2 + opp0 + opp1 + opp2)
    no_cur <- qglm(y ~ own1 + own2 + opp1 + opp2 + win1 + win2)
    current_p <- lr_p(no_cur, full, 1L)
  } else {
    full   <- qglm(y ~ own1 + own2 + opp1 + opp2 + win1 + win2)
    no_own <- qglm(y ~ opp1 + opp2 + win1 + win2)
    no_opp <- qglm(y ~ own1 + own2 + win1 + win2)
    no_win <- qglm(y ~ own1 + own2 + opp1 + opp2)
    current_p <- NA_real_
  }
  co <- coef(full)
  list(own_p = lr_p(no_own, full, 2L), opp_p = lr_p(no_opp, full, 2L), outcome_p = lr_p(no_win, full, 2L),
       current_p = current_p, lag1 = unname(co["own1"]),
       fit_issue = as.integer(max(abs(co[!is.na(co)])) > 15))
}

sessions <- do.call(rbind, lapply(split(d, d$session_id), function(g) {
  f <- fit_session(g)
  data.frame(session_id = g$session_id[1], model_group = g$model_group[1], frame = g$prompt_mode[1],
             own_p = f$own_p, opp_p = f$opp_p, outcome_p = f$outcome_p, current_p = f$current_p,
             lag1 = f$lag1, fit_issue = f$fit_issue, stringsAsFactors = FALSE)
}))

order_mg <- c("opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp")
short <- c(opus = "Opus 4.8", sonnet = "Sonnet 4.6", haiku = "Haiku 4.5", gpt54 = "GPT-5.4",
           gpt54mini = "GPT-5.4-mini", gemini31fl = "Gemini 3.1 FL", gemini3fp = "Gemini 3 FP")
frames <- c("minimalist", "informed")

# Table 2 as printed in the August 2026 preprint: Own, Opp, Outcome, median lag-1 (row order as below)
pub_own <- c(7,7, 3,7, 5,7, 5,0, 3,1, 3,6, 6,7)
pub_opp <- c(7,1, 7,1, 7,2, 7,0, 7,1, 7,4, 7,0)
pub_out <- c(2,1, 3,0, 0,0, 0,0, 0,2, 0,2, 0,0)
pub_lag <- c(1.25,-3.22, 0.39,-5.56, 0.06,-3.66, 0.58,0.03, 0.26,-0.31, 0.67,-1.77, 1.22,-1.06)

rows <- list(); k <- 0L
for (mg in order_mg) for (fr in frames) {
  cell <- sessions[sessions$model_group == mg & sessions$frame == fr, ]
  stopifnot(nrow(cell) == 7L)
  k <- k + 1L
  rows[[k]] <- data.frame(model = unname(short[mg]), frame = fr,
                          own = sum(cell$own_p < .05), opp = sum(cell$opp_p < .05), outcome = sum(cell$outcome_p < .05),
                          current = if (current) sum(cell$current_p < .05) else NA_integer_,
                          lag1_median = median(cell$lag1), fit_issues = sum(cell$fit_issue),
                          stringsAsFactors = FALSE)
}
tab <- do.call(rbind, rows)

outdir <- if (dir.exists("code/table2")) "code/table2/output" else "output"
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
write.csv(sessions, file.path(outdir, paste0("table2_session_fits_", spec, "_R.csv")), row.names = FALSE)
write.csv(tab, file.path(outdir, paste0("table2_", spec, "_R.csv")), row.names = FALSE)

cat("Specification:", spec, "\n")
if (current) cat("Contemporaneous Proteus term significant (p < .05) in", sum(sessions$current_p < .05), "of", nrow(sessions), "sessions.\n")
counts_same <- tab$own == pub_own & tab$opp == pub_opp & tab$outcome == pub_out
lag_same <- abs(round(tab$lag1_median, 2) - pub_lag) < 0.005
shown <- data.frame(model = tab$model, frame = tab$frame,
                    own = sprintf("%d/7", tab$own), opp = sprintf("%d/7", tab$opp), outcome = sprintf("%d/7", tab$outcome))
if (current) shown$current <- sprintf("%d/7", tab$current)
shown$lag1 <- sprintf("%+.2f", tab$lag1_median)
shown$published <- sprintf("%d/7 %d/7 %d/7 %+.2f", pub_own, pub_opp, pub_out, pub_lag)
shown$match <- ifelse(if (current) counts_same else counts_same & lag_same, "yes", "no")
shown$separated <- ifelse(tab$fit_issues > 0, tab$fit_issues, "")
print(shown, row.names = FALSE, right = FALSE)

if (current) {
  shift <- max(abs(tab$own - pub_own), abs(tab$opp - pub_opp), abs(tab$outcome - pub_out))
  cat(sprintf("\nWith the contemporaneous term added, %d of 14 cells keep identical Own/Opp/Outcome counts; the largest change in any count is %d sessions. Companion specification, not a verification target.\n",
              sum(counts_same), shift))
} else {
  n_ok <- sum(counts_same & lag_same)
  if (n_ok == 14L) cat("\nPASS 14/14: Table 2 reproduced\n") else cat(sprintf("\nFAIL %d/14\n", n_ok))
}
