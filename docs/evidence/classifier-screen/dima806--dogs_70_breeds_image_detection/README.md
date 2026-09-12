---
license: apache-2.0
metrics:
- accuracy
base_model:
- google/vit-base-patch16-224-in21k
---
Predicts dogs breed based on an image.

Achieved about 92% accuracy on unseen (test) data.

See [my Kaggle notebook](https://www.kaggle.com/code/dima806/70-dog-breed-image-detection-vit) and [my Medium article](https://medium.com/gitconnected/paws-and-pixels-creating-a-dog-breeds-classifier-with-googles-vision-transformer-431137422830) for more details.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/6449300e3adf50d864095b90/KdUJH1qZauUr5kargckRa.png)

```
Classification report:

                   precision    recall  f1-score   support

           Afghan     0.9753    0.9080    0.9405        87
 African Wild Dog     1.0000    1.0000    1.0000        88
         Airedale     1.0000    0.9885    0.9942        87
American Hairless     0.9841    0.7126    0.8267        87
 American Spaniel     0.9054    0.7701    0.8323        87
          Basenji     0.9659    0.9770    0.9714        87
           Basset     0.9551    0.9770    0.9659        87
           Beagle     0.9659    0.9659    0.9659        88
   Bearded Collie     0.8614    1.0000    0.9255        87
         Bermaise     0.9457    1.0000    0.9721        87
     Bichon Frise     0.9551    0.9770    0.9659        87
         Blenheim     0.9062    1.0000    0.9508        87
       Bloodhound     0.9659    0.9770    0.9714        87
         Bluetick     1.0000    0.9540    0.9765        87
    Border Collie     0.8830    0.9540    0.9171        87
           Borzoi     1.0000    0.9432    0.9708        88
   Boston Terrier     0.5513    0.9773    0.7049        88
            Boxer     1.0000    0.9655    0.9825        87
     Bull Mastiff     0.9655    0.9655    0.9655        87
     Bull Terrier     1.0000    0.9885    0.9942        87
          Bulldog     0.9583    0.2614    0.4107        88
            Cairn     0.8737    0.9540    0.9121        87
        Chihuahua     0.9610    0.8409    0.8970        88
  Chinese Crested     0.9750    0.8966    0.9341        87
             Chow     1.0000    1.0000    1.0000        88
          Clumber     0.9884    0.9770    0.9827        87
         Cockapoo     0.7238    0.8736    0.7917        87
           Cocker     0.9868    0.8621    0.9202        87
           Collie     0.9630    0.8966    0.9286        87
            Corgi     0.9881    0.9540    0.9708        87
           Coyote     0.9560    1.0000    0.9775        87
        Dalmation     0.9560    1.0000    0.9775        87
            Dhole     0.9765    0.9540    0.9651        87
            Dingo     0.8966    0.8966    0.8966        87
         Doberman     0.9333    0.9655    0.9492        87
        Elk Hound     0.9775    1.0000    0.9886        87
   French Bulldog     0.8810    0.8506    0.8655        87
   German Sheperd     0.6803    0.9432    0.7905        88
 Golden Retriever     0.9767    0.9655    0.9711        87
       Great Dane     0.8929    0.8621    0.8772        87
   Great Perenees     0.9667    1.0000    0.9831        87
        Greyhound     0.9750    0.8966    0.9341        87
      Groenendael     0.9062    1.0000    0.9508        87
    Irish Spaniel     0.8173    0.9770    0.8901        87
  Irish Wolfhound     0.9239    0.9770    0.9497        87
 Japanese Spaniel     0.9101    0.9310    0.9205        87
         Komondor     0.9885    0.9885    0.9885        87
      Labradoodle     0.8750    0.6437    0.7417        87
         Labrador     1.0000    0.9091    0.9524        88
            Lhasa     0.9231    0.5517    0.6906        87
         Malinois     0.9756    0.4598    0.6250        87
          Maltese     0.8958    0.9773    0.9348        88
     Mex Hairless     0.7870    0.9770    0.8718        87
     Newfoundland     0.9438    0.9655    0.9545        87
         Pekinese     0.9333    0.9545    0.9438        88
         Pit Bull     0.8969    1.0000    0.9457        87
       Pomeranian     0.9121    0.9540    0.9326        87
           Poodle     0.9759    0.9205    0.9474        88
              Pug     0.9529    0.9310    0.9419        87
        Rhodesian     0.9130    0.9655    0.9385        87
       Rottweiler     0.9556    0.9885    0.9718        87
    Saint Bernard     0.9773    0.9885    0.9829        87
        Schnauzer     0.8684    0.7586    0.8098        87
   Scotch Terrier     0.9506    0.8851    0.9167        87
         Shar_Pei     0.9886    1.0000    0.9943        87
        Shiba Inu     0.9286    0.8966    0.9123        87
         Shih-Tzu     0.6957    0.9195    0.7921        87
   Siberian Husky     0.9667    1.0000    0.9831        87
           Vizsla     0.9355    0.9886    0.9613        88
           Yorkie     0.9457    0.9886    0.9667        88

         accuracy                         0.9192      6104
        macro avg     0.9288    0.9193    0.9161      6104
     weighted avg     0.9288    0.9192    0.9161      6104
```