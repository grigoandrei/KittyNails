import { Link } from "react-router-dom";
import { Check, X } from "lucide-react";

export function BookingSuccess() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center bg-card rounded-2xl shadow-xl border border-border p-8">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h1 className="font-[family-name:var(--font-serif)] text-2xl font-semibold mb-2">
          Payment Successful!
        </h1>
        <p className="text-muted-foreground text-sm mb-6">
          Your deposit has been received and your appointment is confirmed. A
          confirmation email is on its way with all the details.
        </p>
        <div className="bg-secondary rounded-xl p-4 text-sm text-muted-foreground mb-6">
          Need to reach the nail artist? Send a DM on{" "}
          <a
            href="https://www.instagram.com/kittynails_berlin/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary font-medium hover:underline"
          >
            @kittynails_berlin
          </a>
        </div>
        <Link
          to="/"
          className="inline-block bg-primary text-primary-foreground px-6 py-2.5 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}

export function BookingCancelled() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center bg-card rounded-2xl shadow-xl border border-border p-8">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <X className="w-8 h-8 text-red-600" />
        </div>
        <h1 className="font-[family-name:var(--font-serif)] text-2xl font-semibold mb-2">
          Payment Cancelled
        </h1>
        <p className="text-muted-foreground text-sm mb-6">
          Your payment was cancelled and no charge was made. Your appointment
          slot was not reserved. Feel free to try booking again whenever you're
          ready.
        </p>
        <Link
          to="/"
          className="inline-block bg-primary text-primary-foreground px-6 py-2.5 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
