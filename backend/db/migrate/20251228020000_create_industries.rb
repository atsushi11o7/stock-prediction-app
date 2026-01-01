class CreateIndustries < ActiveRecord::Migration[7.2]
  def change
    create_table :industries do |t|
      t.string :name, null: false
      t.references :sector, null: false, foreign_key: true

      t.timestamps
    end

    add_index :industries, [:sector_id, :name], unique: true
  end
end
