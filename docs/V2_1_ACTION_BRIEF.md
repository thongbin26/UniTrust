# V2.1 Grounded Action Brief

For You identifies notices that may matter to a saved profile. The Action
Brief answers what the reviewed official obligation says to do, its deadline
and lifecycle status, amount, location, required documents, exceptions, and
which values remain unknown.

Every factual field comes from `StudentObligation` in reviewed annotations;
the brief never parses a raw notice or invents a recommendation. Missing
fields are explicit. It uses the existing deterministic Asia/Ho_Chi_Minh
deadline resolver and existing Vietnamese UI translations. No generative AI
provider is active or required.

The current limitation is intentional: newly crawled notices without a
reviewed structured annotation can be monitored and shown as fresh, but do not
receive invented Action Brief obligations.
