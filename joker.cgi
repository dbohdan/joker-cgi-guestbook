#! /udd/d/dbohdan/bin/joker

(defn form [action]
  [:form {:method :post :action action}
   [:input {:type :text :name "name"}]
   [:input {:type :text :name "email"}]
   [:textarea {:name "message"}]
   [:input {:type :submit}]])

(defn cgi [env input]
  (str
   "Content-Type: text/html\r\n\r\n"
   "<!doctype html>"
   (joker.hiccup/html
    {:mode :html}
    [:html {:lang "en"}
     [:head [:title "Joker CGI test"]]
     [:body
      [:code (prn-str env)]
      [:hr]
      [:code input]
      (form (get env "SCRIPT_NAME" ""))]])))


(print (cgi (joker.os/env) (slurp *in*)))
