/ MMSR calculation helper functions.
/ Render this once into the configured calculation namespace before running
/ production metrics when operators want a persistent q function surface.
/ Metric templates also define/use the same names defensively so offline plans
/ remain self-contained.

{{ calculation_namespace }}.sumNotional:{[price;size] sum price * size};
{{ calculation_namespace }}.sumSize:{[size] sum size};
{{ calculation_namespace }}.rowCount:{[rows] count rows};
{{ calculation_namespace }}.medianQuotedSpreadBps:{[bid;ask] med 10000 * (ask - bid) % ((ask + bid) % 2)};
{{ calculation_namespace }}.medianTopOfBookDepth:{[bidSize;askSize] med bidSize + askSize};
{{ calculation_namespace }}.weightedAverage:{[weights;values] wavg[weights; values]};
{{ calculation_namespace }}.positiveRatio:{[values] avg values > 0};
{{ calculation_namespace }}.inferAggressorSide:{[tradePrice;mid] ?[tradePrice>mid;1;?[tradePrice<mid;-1;0]]};

{{ calculation_namespace }}.timeBucket:{[t;session;auction;bucket]
    labels:`$string bucket xbar t;
    labels[where (auction = `open) & session = `am]:`AMO;
    labels[where (auction = `close) & session = `am]:`AMC;
    labels[where (auction = `open) & session = `pm]:`PMO;
    labels[where (auction = `close) & session = `pm]:`PMC;
    labels
    };
