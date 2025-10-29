; -------------------------
; Helper functions for scoring components
; -------------------------
(= (ram-score $ram) (/ $ram 32))

(= (price-score $price $budget)
   (if (<= $price $budget)
       (/ (- $budget $price) $budget)
       (* -0.3 (/ (- $price $budget) $budget))))

(= (rating-score $rating $count)
   (* (/ $rating 5.0)
      (if (>= $count 500) 1.0 (/ $count 500))))

; Changed to use nested + with only 2 arguments each
(= (weighted-score $ram-norm $price-norm $rating-norm $prefer)
   (if $prefer
       (+ (+ (* 0.40 $ram-norm) (* 0.35 $price-norm)) (* 0.25 $rating-norm))
       (+ (+ (* 0.25 $ram-norm) (* 0.50 $price-norm)) (* 0.25 $rating-norm))))

; -------------------------
; Main scoring function
; -------------------------
(= (calc-laptop-score $ram $price $budget $rating $count $prefer)
   (weighted-score (ram-score $ram)
                   (price-score $price $budget)
                   (rating-score $rating $count)
                   $prefer))

; -------------------------
; Get all laptop scores
; -------------------------
(= (get-laptop-scores)
   (collapse (match &self (laptop $id $cpu $ram $gpu $price $rating $count)
     (match &self (pref budget $budget)
       (match &self (pref prefer_performance $prefer)
         (scored $id 
                 (calc-laptop-score $ram $price $budget $rating $count $prefer)
                 metta))))))