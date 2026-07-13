(function () {
  var cfg = window.GENZ_SITE || {};

  function qs(sel) {
    return document.querySelector(sel);
  }

  function qsa(sel) {
    return Array.prototype.slice.call(document.querySelectorAll(sel));
  }

  function setActiveNav() {
    var path = window.location.pathname.replace(/\.html$/, "") || "/";
    qsa("[data-nav]").forEach(function (link) {
      var href = link.getAttribute("href") || "";
      var normalized = href.replace(/\.html$/, "");
      if (path === normalized || (path === "/" && normalized === "/index")) {
        link.classList.add("active");
      }
    });
  }

  function injectLegalEntity() {
    var name = cfg.legalEntityName || "[Legal entity name pending]";
    qsa("[data-legal-entity]").forEach(function (el) {
      el.textContent = name;
    });
  }

  function injectSupportEmail() {
    var email = cfg.supportEmail || "zervi@genz.ltd";
    qsa("[data-support-email]").forEach(function (el) {
      if (el.tagName === "A") {
        el.href = "mailto:" + email;
        el.textContent = email;
      } else {
        el.textContent = email;
      }
    });
  }

  function injectFooter() {
    var footer = qs("[data-site-footer]");
    if (!footer) return;

    var entity = cfg.legalEntityName || "[Legal entity name pending]";
    var year = new Date().getFullYear();
    footer.innerHTML =
      '<div class="footer-grid">' +
      '<div>' +
      "<strong>" + (cfg.brandName || "GenZ") + " · " + (cfg.productName || "PlanetX") + "</strong><br>" +
      (cfg.tagline || "AI Career Growth Partner") +
      "<p>© " + year + " " + entity + ". All rights reserved.</p>" +
      "</div>" +
      '<div class="footer-links">' +
      '<a href="/pricing.html">Pricing</a>' +
      '<a href="/legal/privacy.html">Privacy</a>' +
      '<a href="/legal/terms.html">Terms</a>' +
      '<a href="/legal/refund.html">Refund &amp; Cancellation</a>' +
      '<a data-support-email href="mailto:' + (cfg.supportEmail || "zervi@genz.ltd") + '">' +
      (cfg.supportEmail || "zervi@genz.ltd") +
      "</a>" +
      "</div>" +
      "</div>";
  }

  var FALLBACK_PLANS = [
    {
      tier: "free",
      name: "Free",
      price_monthly: 0,
      currency: "USD",
      features: [
        "30 AI chats per day",
        "Basic job matching",
        "3 resume parses per day",
      ],
      upgradable: false,
    },
    {
      tier: "supporter",
      name: "Supporter",
      price_monthly: 1.99,
      currency: "USD",
      features: [
        "100 AI chats per day",
        "Advanced job matching",
        "Unlimited resume parsing",
        "PlanetX supporter badge",
      ],
      upgradable: true,
    },
    {
      tier: "pro",
      name: "Pro",
      price_monthly: 5.99,
      currency: "USD",
      features: [
        "Unlimited AI chats",
        "Full job matching",
        "Unlimited resume parsing",
        "Advanced analytics",
        "Priority support",
      ],
      upgradable: true,
    },
  ];

  function formatPrice(plan) {
    if (!plan.price_monthly) return "$0";
    return "$" + plan.price_monthly;
  }

  var PROVIDER_LABELS = {
    stripe: "Stripe (Card, Apple Pay, Google Pay)",
    paypal: "PayPal",
    airwallex: "Airwallex",
  };

  var PROVIDER_ORDER = ["stripe", "paypal", "airwallex"];

  function renderProviderSelector(planTier, planName) {
    if (planTier === "free") return "";

    var options = PROVIDER_ORDER
      .filter(function (p) {
        // If API has returned available providers, show only those
        if (_availableProviders && _availableProviders.length > 0) {
          return _availableProviders.indexOf(p) !== -1;
        }
        return true; // fallback: show all
      })
      .map(function (p) {
        return (
          '<option value="' +
          p +
          '">' +
          (PROVIDER_LABELS[p] || p) +
          "</option>"
        );
      })
      .join("");

    return (
      '<div class="provider-select" style="margin: 0.5rem 0;">' +
      '<label for="provider-' +
      planTier +
      '" style="font-size:0.85rem;color:var(--text-secondary);">Payment method</label>' +
      '<select id="provider-' +
      planTier +
      '" class="provider-dropdown" style="width:100%;padding:0.4rem;border-radius:6px;border:1px solid var(--border);margin-top:0.25rem;">' +
      options +
      "</select>" +
      "</div>"
    );
  }

  function handleCheckout(provider, tier) {
    var apiBase = cfg.apiBase || "https://api.genz.ltd";

    // Show loading state
    var btn = document.getElementById("btn-" + tier);
    if (btn) {
      btn.textContent = "Redirecting...";
      btn.disabled = true;
    }

    fetch(apiBase + "/v1/payment/checkout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Auth token would be needed in production; for now show API-only flow
      },
      body: JSON.stringify({
        provider: provider,
        tier: tier,
        mode: "payment",
        success_url:
          window.location.origin +
          "/pricing?status=success&session_id={CHECKOUT_SESSION_ID}",
        cancel_url: window.location.origin + "/pricing?status=cancel",
      }),
    })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (err) {
            throw new Error(err.message || "Checkout failed");
          });
        }
        return res.json();
      })
      .then(function (data) {
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
        } else {
          throw new Error("No checkout URL returned");
        }
      })
      .catch(function (err) {
        if (btn) {
          btn.textContent = "Try again";
          btn.disabled = false;
        }
        alert(
          "Payment not available: " +
            (err.message || "Please try again later") +
            "\n\nContact " +
            (cfg.supportEmail || "zervi@genz.ltd")
        );
      });
  }

  function renderPricingCard(plan, popular) {
    var card = document.createElement("article");
    card.className = "card" + (popular ? " popular" : "");

    var providerSelector = renderProviderSelector(plan.tier, plan.name);

    var cta;
    if (plan.tier === "free") {
      cta =
        '<a class="btn btn-secondary" href="' +
        "mailto:" +
        (cfg.supportEmail || "zervi@genz.ltd") +
        "?subject=" +
        encodeURIComponent("PlanetX — Free") +
        '">Get started free</a>';
    } else {
      cta =
        '<div style="display:flex;gap:0.5rem;margin-top:0.5rem;">' +
        '<button id="btn-' +
        plan.tier +
        '" class="btn btn-primary" style="flex:1;" onclick="' +
        "var sel=document.getElementById('provider-" +
        plan.tier +
        "');" +
        "window.__genzCheckout(sel.value,'" +
        plan.tier +
        "')" +
        '">Subscribe</button>' +
        "</div>";
    }

    card.innerHTML =
      (popular ? '<div class="badge">Most popular</div>' : "") +
      "<h3>" +
      plan.name +
      "</h3>" +
      '<div class="price">' +
      formatPrice(plan) +
      '<span> / month</span></div>' +
      "<p>Billed monthly in USD. Cancel anytime.</p>" +
      "<ul>" +
      plan.features
        .map(function (f) {
          return "<li>" + f + "</li>";
        })
        .join("") +
      "</ul>" +
      providerSelector +
      cta;
    return card;
  }

  // Expose checkout handler globally for inline onclick
  window.__genzCheckout = handleCheckout;

  var _availableProviders = [];

  function loadPricing() {
    var grid = qs("#pricing-grid");
    var status = qs("#pricing-status");
    if (!grid) return;

    function paint(plans, source) {
      grid.innerHTML = "";
      plans.forEach(function (plan) {
        grid.appendChild(renderPricingCard(plan, plan.tier === "pro"));
      });
      if (status) {
        var provMsg = "";
        if (_availableProviders.length > 0) {
          provMsg =
            " | Providers: " +
            _availableProviders
              .map(function (p) {
                return PROVIDER_LABELS[p] || p;
              })
              .join(", ");
        }
        status.textContent =
          source === "api"
            ? "Live pricing loaded from Looma API (region=US)." + provMsg
            : "Pricing shown from contract fallback (API unavailable).";
        status.className = "pricing-status " + (source === "api" ? "ok" : "");
      }
    }

    var apiBase = cfg.apiBase || "https://api.genz.ltd";

    // Load available providers first, then pricing
    fetch(apiBase + "/v1/payment/providers?region=US")
      .then(function (res) {
        if (res.ok) return res.json();
        throw new Error("providers unavailable");
      })
      .then(function (data) {
        _availableProviders = data.providers || [];
      })
      .catch(function () {
        _availableProviders = []; // fallback: show all
      })
      .finally(function () {
        // Load pricing plans (always, regardless of providers result)
        fetch(apiBase + "/v1/payment/plans?region=US")
          .then(function (res) {
            if (!res.ok) throw new Error("plans unavailable");
            return res.json();
          })
          .then(function (data) {
            var plans = (data.plans || []).filter(function (p) {
              return p.tier !== "enterprise";
            });
            if (!plans.length) throw new Error("empty plans");
            paint(plans, "api");
          })
          .catch(function () {
            paint(FALLBACK_PLANS, "fallback");
          });
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setActiveNav();
    injectLegalEntity();
    injectSupportEmail();
    injectFooter();
    loadPricing();
  });
})();
