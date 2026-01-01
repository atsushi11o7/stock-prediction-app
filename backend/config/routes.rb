Rails.application.routes.draw do
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # API routes
  namespace :api do

    resources :stocks, only: [:index, :show], param: :ticker, constraints: { ticker: /[^\/]+/ } do
      member do
        get :forecast
      end
    end


    namespace :market do
      get :movers
      get :gainers
      get :losers
      get :overview
    end


    namespace :forecasts do
      get :latest
      get :top_returns
      get :bottom_returns
      get :statistics
    end


    namespace :screening do
      get :high_dividend
      get :low_per
      get :high_roe
      get :value_stocks
      get :growth_stocks
      get :top_market_cap
    end
  end

  # Defines the root path route ("/")
  # root "posts#index"
end
