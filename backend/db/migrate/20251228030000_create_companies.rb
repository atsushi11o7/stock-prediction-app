class CreateCompanies < ActiveRecord::Migration[7.2]
  def change
    create_table :companies do |t|
      t.string :code, null: false
      t.string :ticker, null: false
      t.string :name, null: false
      t.references :sector, null: true, foreign_key: true
      t.references :industry, null: true, foreign_key: true

      t.timestamps
    end

    add_index :companies, :ticker, unique: true
    add_index :companies, :code
  end
end
